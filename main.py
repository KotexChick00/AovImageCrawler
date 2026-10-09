"""
main.py — Entry point của ứng dụng.

Khởi tạo các dependency, chọn mode, chạy ThreadPoolExecutor,
và ghi session log khi hoàn tất.

Menu có thêm:
  - đổi tên file đã tải (modules/utils/renamer.py) — chạy riêng hoặc ngay sau khi tải
  - cập nhật app (.exe) và hero.json từ GitHub (modules/utils/updater.py)
  - báo lỗi của các luồng worker ở cuối phiên (trước đây bị nuốt im lặng)
"""

from __future__ import annotations

import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from modules.core.config import (
    SPLASH_DIR, HEAD_DIR, BUST_DIR, LOG_DIR,
    HERO_WORKERS, HERO_NAME_MAP, APP_VERSION,
)
from modules.core.hero_processor import HeroProcessor
from modules.downloaders.splash_downloader import SplashDownloader
from modules.downloaders.head_downloader import HeadDownloader
from modules.downloaders.bust_downloader import BustDownloader
from modules.utils import renamer, updater
from modules.utils.http_client import HttpClient
from modules.utils.logger import SessionLogger

MODES = {
    "1": "splash",
    "2": "head",
    "3": "bust",
    "4": "all",
    "5": "rename",        # chỉ đổi tên file đã tải
    "6": "all+rename",    # tải tất cả rồi đổi tên
    "7": "update",        # kiểm tra cập nhật app + hero.json từ GitHub
}
DOWNLOAD_MODES = {"splash", "head", "bust", "all"}


# ── UI helpers ────────────────────────────────────────────────────────────────

def select_mode() -> str:
    print("=" * 40)
    print(f"  AoV Image Crawler v{APP_VERSION}")
    print("  Chọn chế độ:")
    print("  1. splash      — chỉ tải splash")
    print("  2. head        — chỉ tải head")
    print("  3. bust        — chỉ tải bust")
    print("  4. all         — tải tất cả (mặc định)")
    print("  5. rename      — đổi tên file đã tải")
    print("  6. all+rename  — tải tất cả rồi đổi tên")
    print("  7. update      — kiểm tra cập nhật (app + hero.json)")
    print("=" * 40)
    choice = input("Nhập lựa chọn [1-7], Enter để chọn all: ").strip()
    mode = MODES.get(choice, "all")
    print(f"→ Chế độ: {mode}\n")
    return mode


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    answer = input(f"{prompt} [{hint}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes", "c", "co", "có")


def fetch_hero_ids() -> list[int]:
    return list(range(105, 800))


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def build_processor() -> HeroProcessor:
    """Khởi tạo dependency tree (manual DI)."""
    http = HttpClient(log_dir=LOG_DIR)
    return HeroProcessor(
        splash=SplashDownloader(http),
        head=HeadDownloader(http),
        bust=BustDownloader(http),
    )


# ── Actions ───────────────────────────────────────────────────────────────────

def run_download(mode: str) -> None:
    # Tạo thư mục đầu ra
    for d in (SPLASH_DIR, HEAD_DIR, BUST_DIR):
        os.makedirs(d, exist_ok=True)

    processor = build_processor()
    hero_ids  = fetch_hero_ids()

    with ThreadPoolExecutor(max_workers=HERO_WORKERS) as executor:
        futures = {
            executor.submit(
                processor.process, hero_id, HERO_NAME_MAP.get(hero_id, str(hero_id)), mode
            ): hero_id
            for hero_id in hero_ids
        }

    report_errors(futures)
    SessionLogger(LOG_DIR).write(datetime.now())


def report_errors(futures: dict) -> None:
    """In lỗi của các luồng worker (nếu có) để không bị nuốt im lặng."""
    errors = [(hero_id, fut.exception()) for fut, hero_id in futures.items() if fut.exception()]
    if not errors:
        return

    print(f"\n[!] {len(errors)} hero bị lỗi khi xử lý:")
    for hero_id, exc in errors[:10]:
        print(f"  - Hero {hero_id}: {type(exc).__name__}: {exc}")
    if len(errors) > 10:
        print(f"  ... và {len(errors) - 10} hero khác")

    first = errors[0][1]
    print("\nChi tiết lỗi đầu tiên:")
    print("".join(traceback.format_exception(type(first), first, first.__traceback__)))


def run_rename(preview_first: bool) -> None:
    dry_run = ask_yes_no("Chỉ xem trước (không đổi tên)?", default=True) if preview_first else False
    print()
    report = renamer.run(dry_run=dry_run)

    # Sau khi xem trước, cho phép đổi thật ngay mà không phải chạy lại
    if dry_run and report is not None and report.renamed:
        if ask_yes_no("\nĐổi tên thật bây giờ?", default=False):
            renamer.run(dry_run=False)


def main() -> None:
    # Tự kiểm tra cập nhật khi mở app (im lặng nếu đã mới nhất / chưa cấu hình / offline)
    if updater.startup_check(ask_yes_no):
        return                       # script cập nhật đã chạy → thoát để thay file

    mode = select_mode()

    if mode in DOWNLOAD_MODES:
        run_download(mode)
    elif mode == "all+rename":
        run_download("all")
        print("\n── Đổi tên file đã tải ──")
        run_rename(preview_first=False)
    elif mode == "rename":
        run_rename(preview_first=True)
    elif mode == "update":
        print("── Kiểm tra cập nhật ──")
        updater.run_checks(ask_yes_no, verbose=True)


if __name__ == "__main__":
    main()