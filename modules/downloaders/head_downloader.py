"""
head_downloader.py — Tải head icon cho hero.
"""

from __future__ import annotations

from modules.core.config import HEAD_URL, HEAD_DIR
from modules.core.id_builder import HeadIDBuilder
from modules.downloaders.base_downloader import BaseAssetDownloader
from modules.utils.http_client import HttpClient


class HeadDownloader(BaseAssetDownloader):
    """Tải head icon (.jpg) từ CDN."""

    def __init__(self, http: HttpClient) -> None:
        super().__init__(http)
        self._builder = HeadIDBuilder()

    @property
    def base_url(self) -> str:
        return HEAD_URL

    @property
    def output_dir(self) -> str:
        return HEAD_DIR

    def build_id(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        return self._builder.build(hero_id, skin_index, evo5)

    def build_base_id(self, hero_id: int) -> str:
        return self._builder.build_base(hero_id)