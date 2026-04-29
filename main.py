"""
main.py — Entry point của ứng dụng.

Khởi tạo các dependency, chọn mode, chạy ThreadPoolExecutor,
và ghi session log khi hoàn tất.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from modules.core.config import (
    SPLASH_DIR, HEAD_DIR, FRAME_DIR, LOG_DIR,
    HERO_WORKERS,
)
from modules.core.hero_processor import HeroProcessor
from modules.downloaders.splash_downloader import SplashDownloader
from modules.downloaders.head_downloader import HeadDownloader
from modules.downloaders.frame_downloader import FrameDownloader
from modules.utils.http_client import HttpClient
from modules.utils.logger import SessionLogger


# ── UI helpers ────────────────────────────────────────────────────────────────

def select_mode() -> str:
    print("=" * 40)
    print("  Chọn chế độ tải:")
    print("  1. splash  — chỉ tải splash")
    print("  2. head    — chỉ tải head")
    print("  3. frame   — chỉ tải frame")
    print("  4. all     — tải tất cả (mặc định)")
    print("=" * 40)
    choice = input("Nhập lựa chọn [1/2/3/4], Enter để chọn all: ").strip()
    mapping = {"1": "splash", "2": "head", "3": "frame"}
    mode = mapping.get(choice, "all")
    print(f"→ Chế độ: {mode}\n")
    return mode


def fetch_hero_ids() -> list[int]:
    return list(range(105, 800))


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def build_processor() -> HeroProcessor:
    """Khởi tạo dependency tree (manual DI)."""
    http = HttpClient(log_dir=LOG_DIR)
    return HeroProcessor(
        splash=SplashDownloader(http),
        head=HeadDownloader(http),
        frame=FrameDownloader(http),
    )


def main() -> None:
    mode = select_mode()

    # Tạo thư mục đầu ra
    for d in (SPLASH_DIR, HEAD_DIR, FRAME_DIR):
        os.makedirs(d, exist_ok=True)

    processor = build_processor()
    hero_ids  = fetch_hero_ids()

    with ThreadPoolExecutor(max_workers=HERO_WORKERS) as executor:
        for hero_id in hero_ids:
            executor.submit(processor.process, hero_id, mode)

    SessionLogger(LOG_DIR).write(datetime.now())


if __name__ == "__main__":
    main()
