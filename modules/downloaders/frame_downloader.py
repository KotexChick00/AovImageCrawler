"""
frame_downloader.py — Tải frame border cho hero.

Xử lý thêm hai trường hợp đặc biệt:
  1. Flowborn heroes → dùng gender suffix thay vì skin index
  2. SPECIAL_FRAME   → file ID cứng, tải thẳng theo hero_id
"""

from __future__ import annotations

import os

from modules.core.config import (
    HEAD_URL, FRAME_DIR,
    FLOWBORN_SPECIAL_HERO_ID,
    FLOWBORN_GENDER_SUFFIX_FRAME,
    SPECIAL_FRAME,
)
from modules.core.id_builder import FrameIDBuilder
from modules.core.miss_counter import MissCounter
from modules.downloaders.base_downloader import BaseAssetDownloader
from modules.utils.http_client import HttpClient


class FrameDownloader(BaseAssetDownloader):
    """Tải frame border (.jpg) từ CDN."""

    def __init__(self, http: HttpClient) -> None:
        super().__init__(http)
        self._builder = FrameIDBuilder()

    # ── Abstract implementations ──────────────────────────────────────────────

    @property
    def base_url(self) -> str:
        return HEAD_URL

    @property
    def output_dir(self) -> str:
        return FRAME_DIR

    def build_id(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        return self._builder.build(hero_id, skin_index, evo5)

    def build_base_id(self, hero_id: int) -> str:
        return self._builder.build_base(hero_id)

    # ── Override process_hero ─────────────────────────────────────────────────

    def process_hero(self, hero_id: int, miss_counter: MissCounter) -> None:
        hero_dir = os.path.join(self.output_dir, str(hero_id))

        # Flowborn: quy tắc đặt tên hoàn toàn khác → thoát sớm sau khi tải
        if hero_id in FLOWBORN_SPECIAL_HERO_ID:
            self._download_flowborn(hero_id, hero_dir)
            return

        # Special frames (file ID cứng)
        self._download_special_frames(hero_id, hero_dir)

        # Frame thường — giống base template
        base_id = self.build_base_id(hero_id)
        result  = self._fetch(base_id, hero_dir)
        if result == "missing" and not os.path.exists(os.path.join(hero_dir, f"{base_id}.jpg")):
            return

        self._download_skins(hero_id, hero_dir, miss_counter)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _download_flowborn(self, hero_id: int, hero_dir: str) -> None:
        for gender in FLOWBORN_GENDER_SUFFIX_FRAME:
            file_id = self._builder.build_flowborn(hero_id, gender)
            self._fetch(file_id, hero_dir)

    def _download_special_frames(self, hero_id: int, hero_dir: str) -> None:
        for file_id in SPECIAL_FRAME:
            if FrameIDBuilder.parse_hero_id_from_special(file_id) == hero_id:
                self._fetch(file_id, hero_dir)