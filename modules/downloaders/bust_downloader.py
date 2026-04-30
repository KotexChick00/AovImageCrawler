"""
BUST_downloader.py — Tải BUST border cho hero.

Xử lý thêm hai trường hợp đặc biệt:
  1. Flowborn heroes → dùng gender suffix thay vì skin index
  2. SPECIAL_BUST   → file ID cứng, tải thẳng theo hero_id
"""

from __future__ import annotations

import os

from modules.core.config import (
    HEAD_URL, BUST_DIR,
    FLOWBORN_SPECIAL_HERO_ID,
    FLOWBORN_GENDER_SUFFIX_BUST,
    SPECIAL_BUST,
)
from modules.core.id_builder import BustIDBuilder
from modules.core.miss_counter import MissCounter
from modules.downloaders.base_downloader import BaseAssetDownloader
from modules.utils.http_client import HttpClient


class BustDownloader(BaseAssetDownloader):
    """Tải BUST border (.jpg) từ CDN."""

    def __init__(self, http: HttpClient) -> None:
        super().__init__(http)
        self._builder = BustIDBuilder()

    # ── Abstract implementations ──────────────────────────────────────────────

    @property
    def base_url(self) -> str:
        return HEAD_URL

    @property
    def output_dir(self) -> str:
        return BUST_DIR

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

        # Special BUSTs (file ID cứng)
        self._download_special_BUSTs(hero_id, hero_dir)

        # BUST thường — giống base template
        base_id = self.build_base_id(hero_id)
        result  = self._fetch(base_id, hero_dir)
        if result == "missing" and not os.path.exists(os.path.join(hero_dir, f"{base_id}.jpg")):
            return

        self._download_skins(hero_id, hero_dir, miss_counter)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _download_flowborn(self, hero_id: int, hero_dir: str) -> None:
        for gender in FLOWBORN_GENDER_SUFFIX_BUST:
            file_id = self._builder.build_flowborn(hero_id, gender)
            self._fetch(file_id, hero_dir)

    def _download_special_BUSTs(self, hero_id: int, hero_dir: str) -> None:
        for file_id in SPECIAL_BUST:
            if BustIDBuilder.parse_hero_id_from_special(file_id) == hero_id:
                self._fetch(file_id, hero_dir)