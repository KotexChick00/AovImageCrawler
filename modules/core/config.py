"""
config.py — Tập trung toàn bộ hằng số và cấu hình của ứng dụng.
Thay đổi URL, thư mục, giới hạn... tại đây, không cần chạm vào logic.
"""

from __future__ import annotations

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
FLOWBORN_GENDER_SUFFIX_FRAME = ["m", "f"]

# ── Special frames (raw file IDs) ─────────────────────────────────────────────
SPECIAL_FRAME = ["301270_B51"]

# ── Output directories ────────────────────────────────────────────────────────
OUTPUT_DIR  = "."
SPLASH_DIR  = f"{OUTPUT_DIR}/splash"
HEAD_DIR    = f"{OUTPUT_DIR}/head"
FRAME_DIR   = f"{OUTPUT_DIR}/frame"
LOG_DIR     = f"{OUTPUT_DIR}/logs"

# ── Threading ─────────────────────────────────────────────────────────────────
HERO_WORKERS       = 10
B_SUFFIX_WORKERS   = 5