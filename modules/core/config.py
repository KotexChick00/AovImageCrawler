"""
config.py — Tập trung toàn bộ hằng số và cấu hình của ứng dụng.
Thay đổi URL, thư mục, giới hạn... tại đây, không cần chạm vào logic.
"""

from __future__ import annotations

import json
import os
import sys

# ── URLs ──────────────────────────────────────────────────────────────────────
SPLASH_URL = "https://dl.ops.kgtw.garenanow.com/CHT/HeroTrainingLoadingNew_B36/"
HEAD_URL   = "https://dl.ops.kgtw.garenanow.com/CHT/HeroHeadPath/"

# ── ID builders params ────────────────────────────────────────────────────────
HEAD_REQUIRED_PREFIX      = "30"
HEAD_ICON_REQUIRED_SUFFIX = "head"
EVO5_ALT_SUFFIX           = "_2"

# ── Scan ranges ───────────────────────────────────────────────────────────────
SUFFIX_RANGE   = range(100)       # skin index 00–99
B_SUFFIX_RANGE = range(36, 100)   # B36–B99 (splash only)

# ── Cách kiểm tra "đã tải chưa" ───────────────────────────────────────────────
# "disk": file {file_id}.* còn trên đĩa là đã tải (cách cũ). Xóa file → tự tải lại.
#         Nhưng file bị đổi tên (kể cả bởi renamer) sẽ bị coi là chưa tải.
# "url" : URL nằm trong logs/downloaded_urls.txt là đã tải. Đổi tên/di chuyển file
#         thoải mái, nhưng xóa file mà giữ log thì KHÔNG tự tải lại.
DUPLICATE_CHECK = "disk"

# ── Miss-counter limit ────────────────────────────────────────────────────────
MISS_LIMIT = 15

# ── EVO5 skins (hero_id, skin_index) ─────────────────────────────────────────
EVO5_SKIN_LIST: list[tuple[int, int]] = [
    (116, 20),
    (133, 11),
    (167,  7),
]

# ── Flowborn heroes ───────────────────────────────────────────────────────────
FLOWBORN_SPECIAL_HERO_ID    = [582, 584]
FLOWBORN_UNIQUE_SUFFIX_ID   = "00"
FLOWBORN_GENDER_SUFFIX_BUST = ["m", "f"]

# ── Output directories ────────────────────────────────────────────────────────
OUTPUT_DIR  = "."
SPLASH_DIR  = f"{OUTPUT_DIR}/splash"
HEAD_DIR    = f"{OUTPUT_DIR}/head"
BUST_DIR   = f"{OUTPUT_DIR}/bust"
LOG_DIR     = f"{OUTPUT_DIR}/logs"

# ── Threading ─────────────────────────────────────────────────────────────────
HERO_WORKERS       = 10
B_SUFFIX_WORKERS   = 5
# ── Hero data loading ─────────────────────────────────────────────────────────
def _hero_json_candidates() -> list[str]:
    """Các vị trí có thể chứa hero.json, theo thứ tự ưu tiên."""
    here = os.path.dirname(os.path.abspath(__file__))
    paths: list[str] = []

    if getattr(sys, "frozen", False):
        # Chạy từ bản đóng gói (PyInstaller): ưu tiên file nằm cạnh file .exe
        # để người dùng có thể sửa/cập nhật hero.json mà không cần build lại.
        paths.append(os.path.join(os.path.dirname(sys.executable), "hero.json"))
        # File được đóng gói kèm bằng --add-data "hero.json;."
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            paths.append(os.path.join(meipass, "hero.json"))

    paths.append(os.path.join(os.getcwd(), "hero.json"))          # thư mục đang chạy
    paths.append(os.path.join(here, "../../hero.json"))           # layout mã nguồn gốc
    return [os.path.normpath(p) for p in paths]


def _load_hero_data() -> dict[int, str]:
    """Load hero name mapping from hero.json (id -> name)."""
    candidates = _hero_json_candidates()
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                heroes = json.load(f)
            return {int(h["id"]): h["name"] for h in heroes}
        except Exception as e:
            print(f"Warning: Could not parse {path}: {e}")
            return {}

    print("Warning: hero.json not found. Đã tìm ở:")
    for p in candidates:
        print(f"  - {p}")
    return {}

HERO_NAME_MAP: dict[int, str] = _load_hero_data()