"""
splash_downloader.py — Tải splash art cho hero.

Ngoài skin thường, còn có B-suffix variant chạy song song
(không bị ảnh hưởng bởi miss counter).
"""

from __future__ import annotations

from modules.core.config import SPLASH_URL, SPLASH_DIR
from modules.core.id_builder import SplashIDBuilder
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

    def build_b_id(self, hero_id: int, skin_index: int, b_suffix: int) -> str:
        # Splash B-variant luôn dùng skin 0 ({hero_id}00_B{n}) nên bỏ qua skin_index.
        return self._builder.build_b_variant(hero_id, b_suffix)