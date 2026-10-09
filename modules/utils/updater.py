"""
updater.py — Kiểm tra và cập nhật từ GitHub:
  1. File .exe của app   (qua GitHub Releases)
  2. hero.json           (tải trực tiếp từ nhánh trong repo)

Cấu hình ở config.py: GITHUB_REPO, GITHUB_BRANCH, APP_VERSION, EXE_ASSET_NAME.

Cập nhật exe:
  - Tải bản mới về `<tên exe>.new`, xác minh SHA-256 nếu release có file `<tên exe>.sha256`.
  - Windows không cho ghi đè exe đang chạy → sinh một file .bat nhỏ, đợi app thoát,
    thay file rồi mở lại app.
  - Chỉ tải từ URL thuộc đúng repo đã cấu hình.
Cập nhật hero.json:
  - Kiểm tra định dạng, hỏi xác nhận, sao lưu bản cũ thành hero.json.bak,
    ghi nguyên tử rồi nạp lại HERO_NAME_MAP tại chỗ (không cần mở lại app).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Callable

import requests

from modules.core import config

AskFn = Callable[[str, bool], bool]     # (câu hỏi, mặc định) -> đồng ý?

API_TIMEOUT      = 10
DOWNLOAD_TIMEOUT = 30
_PLACEHOLDER     = "your-user/"


class UpdateError(Exception):
    """Lỗi có thể giải thích cho người dùng (mạng, định dạng, xác minh...)."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_configured() -> bool:
    repo = config.GITHUB_REPO
    return bool(repo) and "/" in repo and not repo.startswith(_PLACEHOLDER)


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _is_windows() -> bool:
    return os.name == "nt"


def parse_version(tag: str) -> tuple[int, ...]:
    """'v1.2.3' / '1.2' → (1, 2, 3). Bỏ hậu tố như -beta."""
    return tuple(int(n) for n in re.findall(r"\d+", tag.split("-")[0]))


def is_newer(remote: tuple[int, ...], local: tuple[int, ...]) -> bool:
    n = max(len(remote), len(local))
    pad = lambda v: v + (0,) * (n - len(v))        # (1,0) và (1,0,0) coi như bằng nhau
    return pad(remote) > pad(local)


def _norm(name: str) -> str:
    """GitHub đổi dấu cách trong tên asset thành dấu chấm → so khớp bỏ qua ký tự đặc biệt."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _require_repo_url(url: str) -> None:
    if not url.startswith(f"https://github.com/{config.GITHUB_REPO}/releases/download/"):
        raise UpdateError("URL tải không thuộc repo đã cấu hình — đã hủy.")


def _silent_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


# ── Release ───────────────────────────────────────────────────────────────────

@dataclass
class ReleaseInfo:
    tag: str
    version: tuple[int, ...]
    notes: str
    page_url: str
    exe_name: str | None = None
    exe_url: str | None = None
    exe_size: int | None = None
    checksum_url: str | None = None


def _parse_release(data: dict) -> ReleaseInfo:
    tag = data.get("tag_name") or ""
    version = parse_version(tag)
    if not version:
        raise UpdateError(f"không đọc được số phiên bản từ tag {tag!r}")

    assets = data.get("assets") or []
    wanted = _norm(config.EXE_ASSET_NAME)
    exe = next((a for a in assets if _norm(a.get("name", "")) == wanted), None)
    if exe is None:                                  # chỉ có đúng một .exe thì dùng luôn
        exes = [a for a in assets if a.get("name", "").lower().endswith(".exe")]
        exe = exes[0] if len(exes) == 1 else None

    info = ReleaseInfo(
        tag=tag, version=version,
        notes=data.get("body") or "",
        page_url=data.get("html_url") or f"https://github.com/{config.GITHUB_REPO}/releases",
    )
    if exe:
        info.exe_name = exe.get("name")
        info.exe_url  = exe.get("browser_download_url")
        info.exe_size = exe.get("size")
        want_chk = _norm(exe["name"]) + "sha256"
        chk = next((a for a in assets if _norm(a.get("name", "")) == want_chk), None)
        info.checksum_url = chk.get("browser_download_url") if chk else None
    return info


def fetch_latest_release() -> ReleaseInfo:
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest"
    try:
        r = requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=API_TIMEOUT)
    except requests.RequestException as exc:
        raise UpdateError(f"không kết nối được GitHub ({type(exc).__name__})") from exc
    if r.status_code == 404:
        raise UpdateError("repo không tồn tại, là repo riêng tư, hoặc chưa có release nào")
    if r.status_code == 403:
        raise UpdateError("GitHub từ chối (thường do quá giới hạn lượt gọi) — thử lại sau")
    if r.status_code != 200:
        raise UpdateError(f"GitHub trả về HTTP {r.status_code}")
    try:
        return _parse_release(r.json())
    except ValueError as exc:
        raise UpdateError("phản hồi từ GitHub không phải JSON hợp lệ") from exc


# ── Tải & xác minh ────────────────────────────────────────────────────────────

def download_file(url: str, dest: str, expected_size: int | None = None) -> None:
    _require_repo_url(url)
    part = dest + ".part"
    try:
        with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length") or expected_size or 0)
            done, last = 0, -1
            with open(part, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done * 100 // total
                        if pct != last and pct % 5 == 0:
                            print(f"\r  Đang tải... {pct}%", end="", flush=True)
                            last = pct
        print()
    except (requests.RequestException, OSError) as exc:
        _silent_remove(part)
        raise UpdateError(f"tải file thất bại ({type(exc).__name__}: {exc})") from exc

    if expected_size and os.path.getsize(part) != expected_size:
        _silent_remove(part)
        raise UpdateError("kích thước file tải về không khớp với release")
    os.replace(part, dest)


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _read_expected_hash(url: str) -> str:
    _require_repo_url(url)
    try:
        r = requests.get(url, timeout=API_TIMEOUT)
    except requests.RequestException as exc:
        raise UpdateError(f"không tải được file .sha256 ({type(exc).__name__})") from exc
    m = re.search(r"\b[a-fA-F0-9]{64}\b", r.text) if r.status_code == 200 else None
    if not m:
        raise UpdateError("file .sha256 không đọc được — đã hủy để an toàn")
    return m.group(0).lower()


# ── Cập nhật exe ──────────────────────────────────────────────────────────────

def stage_exe_update(info: ReleaseInfo) -> str:
    """Tải bản mới cạnh exe hiện tại và xác minh. Trả về đường dẫn file `.new`."""
    new_path = sys.executable + ".new"
    print(f"  Tải {info.exe_name} ({info.tag})...")
    download_file(info.exe_url, new_path, info.exe_size)

    if info.checksum_url:
        expected = _read_expected_hash(info.checksum_url)
        if sha256_of(new_path) != expected:
            _silent_remove(new_path)
            raise UpdateError("SHA-256 không khớp — file có thể bị lỗi hoặc bị can thiệp, đã hủy")
        print("  ✓ Đã xác minh SHA-256.")
    else:
        print("  ! Release không có file .sha256 → không thể xác minh toàn vẹn file.")
    return new_path


def build_swap_script(old_exe: str, new_exe: str) -> str:
    """Script .bat: đợi app thoát → thay file → mở lại app → tự xóa."""
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "title AoV Image Crawler - dang cap nhat",
        f'set "OLD={old_exe}"',
        f'set "NEW={new_exe}"',
        "set /a tries=0",
        ":retry",
        "timeout /t 1 /nobreak >nul",
        'move /Y "%NEW%" "%OLD%" >nul 2>&1',
        "if not errorlevel 1 goto done",
        "set /a tries+=1",
        "if %tries% lss 30 goto retry",
        "echo Cap nhat that bai: khong thay duoc file. Ban moi van nam o: %NEW%",
        "pause",
        "exit /b 1",
        ":done",
        'start "" "%OLD%"',
        '(goto) 2>nul & del "%~f0"',
        "",
    ]
    return "\r\n".join(lines)


def apply_exe_update(new_exe: str) -> None:
    """Khởi chạy script thay file. Người gọi PHẢI thoát app ngay sau đó."""
    script = os.path.join(tempfile.gettempdir(), "aov_crawler_update.bat")
    with open(script, "w", encoding="utf-8", newline="") as f:
        f.write(build_swap_script(sys.executable, new_exe))
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(["cmd.exe", "/c", script], creationflags=flags, close_fds=True)


def _print_notes(notes: str, max_lines: int = 12) -> None:
    lines = [ln.rstrip() for ln in notes.splitlines() if ln.strip()]
    for ln in lines[:max_lines]:
        print(f"    {ln[:100]}")
    if len(lines) > max_lines:
        print("    ...")


def update_app(ask: AskFn, verbose: bool = True) -> bool:
    """Trả về True nếu đã khởi chạy cập nhật và app cần thoát ngay."""
    if not _is_frozen() and not verbose:
        return False                 # chạy từ mã nguồn: không tự cập nhật exe, khỏi nhắc mỗi lần mở
    info = fetch_latest_release()
    current = parse_version(config.APP_VERSION)
    if not is_newer(info.version, current):
        if verbose:
            print(f"  App đã là bản mới nhất (v{config.APP_VERSION}).")
        return False

    print(f"  Có bản mới: {info.tag} (hiện tại v{config.APP_VERSION})")
    _print_notes(info.notes)

    if not _is_frozen():
        print("  Đang chạy từ mã nguồn → cập nhật bằng `git pull`.")
        return False
    if not _is_windows():
        print(f"  Tự cập nhật exe chỉ hỗ trợ Windows. Tải tại: {info.page_url}")
        return False
    if not info.exe_url:
        print(f"  Release không đính kèm file .exe. Xem: {info.page_url}")
        return False
    if not ask("  Cập nhật ngay?", False):
        return False

    new_exe = stage_exe_update(info)
    apply_exe_update(new_exe)
    print("  Đang khởi động lại để hoàn tất cập nhật...")
    return True


# ── Cập nhật hero.json ────────────────────────────────────────────────────────

def _validate_heroes(data) -> dict[int, str]:
    if not isinstance(data, list) or not data:
        raise UpdateError("hero.json trên repo không phải danh sách hero hợp lệ")
    heroes: dict[int, str] = {}
    for h in data:
        try:
            heroes[int(h["id"])] = str(h["name"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UpdateError("hero.json trên repo có phần tử thiếu 'id' hoặc 'name'") from exc
    return heroes


def fetch_remote_hero_json() -> tuple[bytes, dict[int, str]]:
    url = (f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/"
           f"{config.GITHUB_BRANCH}/{config.HERO_JSON_PATH_IN_REPO}")
    try:
        r = requests.get(url, timeout=API_TIMEOUT)
    except requests.RequestException as exc:
        raise UpdateError(f"không kết nối được GitHub ({type(exc).__name__})") from exc
    if r.status_code == 404:
        raise UpdateError(f"không thấy {config.HERO_JSON_PATH_IN_REPO} trên nhánh {config.GITHUB_BRANCH}")
    if r.status_code != 200:
        raise UpdateError(f"GitHub trả về HTTP {r.status_code}")
    try:
        heroes = _validate_heroes(r.json())
    except ValueError as exc:
        raise UpdateError("hero.json trên repo không phải JSON hợp lệ") from exc
    return r.content, heroes


def diff_heroes(local: dict[int, str], remote: dict[int, str]) -> tuple[list[int], list[int], list[int]]:
    added   = sorted(set(remote) - set(local))
    removed = sorted(set(local) - set(remote))
    renamed = sorted(i for i in set(local) & set(remote) if local[i] != remote[i])
    return added, removed, renamed


def _hero_json_target() -> str:
    found  = config.find_hero_json()
    meipass = getattr(sys, "_MEIPASS", None)
    in_temp = bool(found and meipass and os.path.abspath(found).startswith(os.path.abspath(meipass)))
    # Bản nằm trong thư mục giải nén tạm của PyInstaller sẽ mất khi thoát → ghi cạnh exe
    return found if found and not in_temp else config.default_hero_json_path()


def update_hero_json(ask: AskFn, verbose: bool = True) -> bool:
    raw, remote = fetch_remote_hero_json()
    local = dict(config.HERO_NAME_MAP)
    added, removed, renamed = diff_heroes(local, remote)
    if not (added or removed or renamed):
        if verbose:
            print(f"  hero.json đã khớp với repo ({len(remote)} hero).")
        return False

    print("  hero.json trên repo khác bản hiện tại:")
    if added:
        names = ", ".join(f"{i}={remote[i]}" for i in added[:8])
        print(f"    + {len(added)} hero mới: {names}{' ...' if len(added) > 8 else ''}")
    if renamed:
        print(f"    ~ {len(renamed)} hero đổi tên: " +
              ", ".join(f"{i}: {local[i]}→{remote[i]}" for i in renamed[:5]) +
              (" ..." if len(renamed) > 5 else ""))
    if removed:
        print(f"    - {len(removed)} hero không còn trên repo: {removed[:10]}")
    if not ask("  Cập nhật hero.json?", True):
        return False

    target = _hero_json_target()
    if os.path.isfile(target):
        shutil.copy2(target, target + ".bak")
    tmp = target + ".tmp"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, target)

    config.HERO_NAME_MAP.clear()             # cập nhật tại chỗ để các module đã import thấy ngay
    config.HERO_NAME_MAP.update(remote)
    print(f"  ✓ Đã cập nhật {target} ({len(remote)} hero). Bản cũ: hero.json.bak")
    return True


# ── Entry points ──────────────────────────────────────────────────────────────

def run_checks(ask: AskFn, verbose: bool = True) -> bool:
    """Kiểm tra app + hero.json. Trả về True nếu app cần thoát để cập nhật."""
    if not is_configured():
        if verbose:
            print("  Chưa cấu hình GITHUB_REPO trong config.py.")
        return False

    steps = (("app", update_app), ("hero.json", update_hero_json))
    for label, step in steps:
        try:
            if step(ask, verbose):
                if label == "app":
                    return True
        except UpdateError as exc:
            print(f"  [Cập nhật {label}] {exc}" if verbose else f"  (Không kiểm tra được cập nhật: {exc})")
            if not verbose:
                return False
        except Exception as exc:                     # không bao giờ để lỗi cập nhật làm sập app
            print(f"  [Cập nhật {label}] lỗi không mong đợi: {type(exc).__name__}: {exc}")
            if not verbose:
                return False
    return False


def startup_check(ask: AskFn) -> bool:
    """Gọi khi mở app. Im lặng nếu đã mới nhất hoặc chưa cấu hình."""
    if not config.UPDATE_CHECK_ON_START or not is_configured():
        return False
    return run_checks(ask, verbose=False)