"""
hero_processor.py — Điều phối việc tải tất cả asset của một hero.

HeroProcessor giữ tham chiếu đến các downloader và tạo MissCounter
riêng cho mỗi loại asset, đảm bảo counter của splash không ảnh hưởng
đến counter của head/frame.
"""

from __future__ import annotations

from modules.core.config import MISS_LIMIT
from modules.core.miss_counter import MissCounter
from modules.downloaders.splash_downloader import SplashDownloader
from modules.downloaders.head_downloader import HeadDownloader
from modules.downloaders.bust_downloader import BustDownloader


class HeroProcessor:
    """
    Điều phối tải asset cho một hero theo mode được chọn.

    mode: 'splash' | 'head' | 'bust' | 'all'
    """

    def __init__(
        self,
        splash: SplashDownloader,
        head: HeadDownloader,
        bust: BustDownloader,
        miss_limit: int = MISS_LIMIT,
    ) -> None:
        self._splash     = splash
        self._head       = head
        self._bust       = bust
        self._miss_limit = miss_limit

    def process(self, hero_id: int, mode: str) -> None:
        """Tải tất cả asset cần thiết cho hero_id theo mode."""
        if mode in ("splash", "all"):
            self._splash.process_hero(hero_id, MissCounter(self._miss_limit))
        if mode in ("head", "all"):
            self._head.process_hero(hero_id, MissCounter(self._miss_limit))
        if mode in ("bust", "all"):
            self._bust.process_hero(hero_id, MissCounter(self._miss_limit))