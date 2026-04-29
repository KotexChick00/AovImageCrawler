"""
splash_downloader.py — Tải splash art cho hero.

Ngoài skin thường, còn có B-suffix variant chạy song song
(không bị ảnh hưởng bởi miss counter).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from modules.core.config import SPLASH_URL, SPLASH_DIR, B_SUFFIX_RANGE, B_SUFFIX_WORKERS
from modules.core.id_builder import SplashIDBuilder
from modules.core.miss_counter import MissCounter
from modules.downloaders.base_downloader import BaseAssetDownloader
from modules.utils.http_client import HttpClient


class SplashDownloader(BaseAssetDownloader):
    """Tải splash art (.jpg) từ CDN."""

    def __init__(self, http: HttpClient) -> None:
        super().__init__(http)
        self._builder = SplashIDBuilder()

    # ── Abstract implementations ──────────────────────────────────────────────

    @property
    def base_url(self) -> str:
        return SPLASH_URL

    @property
    def output_dir(self) -> str:
        return SPLASH_DIR

    def build_id(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        return self._builder.build(hero_id, skin_index, evo5)

    def build_base_id(self, hero_id: int) -> str:
        return self._builder.build_base(hero_id)

    # ── Override process_hero để thêm B-suffix ────────────────────────────────

    def process_hero(self, hero_id: int, miss_counter: MissCounter) -> None:
        """Tải skin thường rồi chạy song song B-suffix variants."""
        import os
        hero_dir = self.output_dir + f"/{hero_id}"

        base_id = self.build_base_id(hero_id)
        result  = self._fetch(base_id, hero_dir)

        if result == "missing" and not os.path.exists(f"{hero_dir}/{base_id}.jpg"):
            return

        # Skin variants (tuần tự để miss_counter hoạt động đúng)
        self._download_skins(hero_id, hero_dir, miss_counter)

        # B-suffix variants chạy song song độc lập
        with ThreadPoolExecutor(max_workers=B_SUFFIX_WORKERS) as pool:
            for b_suffix in B_SUFFIX_RANGE:
                pool.submit(self._download_b_variant, hero_id, hero_dir, b_suffix)

    # ── Private ───────────────────────────────────────────────────────────────

    def _download_b_variant(self, hero_id: int, hero_dir: str, b_suffix: int) -> None:
        file_id = self._builder.build_b_variant(hero_id, b_suffix)
        self._fetch(file_id, hero_dir)