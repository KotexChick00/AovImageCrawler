"""
base_downloader.py — Abstract base cho tất cả asset downloader.

Định nghĩa template method pattern:
  process_hero() → gọi _download_base() và _download_skins()
Subclass chỉ cần implement các phương thức trừu tượng.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
import glob

from modules.core.config import EVO5_SKIN_LIST, SUFFIX_RANGE
from modules.core.miss_counter import MissCounter
from modules.utils.http_client import HttpClient, DownloadStatus


class BaseAssetDownloader(ABC):
    """
    Base class cho việc tải một loại asset (splash / head / frame).

    Subclass phải implement:
      - base_url      : URL prefix
      - output_dir    : thư mục gốc lưu file
      - build_id()    : tạo file ID từ hero_id + skin_index
      - build_base_id(): tạo file ID cho skin index 0
    """

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    # ── Abstract interface ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @property
    @abstractmethod
    def output_dir(self) -> str: ...

    @abstractmethod
    def build_id(self, hero_id: int, skin_index: int, evo5: bool = False) -> str: ...

    @abstractmethod
    def build_base_id(self, hero_id: int) -> str: ...

    # ── Template method ───────────────────────────────────────────────────────

    def process_hero(self, hero_id: int, miss_counter: MissCounter) -> None:
        """Tải skin base rồi duyệt qua toàn bộ skin variant."""
        hero_dir = os.path.join(self.output_dir, str(hero_id))

        base_id = self.build_base_id(hero_id)
        result  = self._fetch(base_id, hero_dir)

        # Nếu skin 0 không tồn tại và cũng chưa có trên đĩa (bất kể đuôi) → hero không tồn tại
        if result == "missing" and not glob.glob(os.path.join(hero_dir, f"{base_id}.*")):
            return

        self._download_skins(hero_id, hero_dir, miss_counter)

    # ── Skin loop ─────────────────────────────────────────────────────────────

    def _download_skins(
        self, hero_id: int, hero_dir: str, miss_counter: MissCounter
    ) -> None:
        for skin_index in SUFFIX_RANGE:
            if skin_index == 0:
                continue
            if miss_counter.stopped:
                asset_type = self.__class__.__name__
                print(f"[{asset_type}] Hero {hero_id}: miss limit reached, stopping skin loop.")
                break
            self._process_skin(hero_id, hero_dir, skin_index, miss_counter)

    def _process_skin(
        self,
        hero_id: int,
        hero_dir: str,
        skin_index: int,
        miss_counter: MissCounter,
    ) -> None:
        file_id = self.build_id(hero_id, skin_index)
        result  = self._fetch(file_id, hero_dir)

        if result == "missing":
            miss_counter.miss()
        else:
            miss_counter.hit()
            if self._is_evo5(hero_id, skin_index):
                evo_id = self.build_id(hero_id, skin_index, evo5=True)
                self._fetch(evo_id, hero_dir)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fetch(self, file_id: str, save_dir: str) -> DownloadStatus:
        # URL nguồn luôn dùng .jpg (theo quy ước endpoint của server), nhưng nội
        # dung trả về đôi khi thực chất là .png/.webp/... — HttpClient sẽ tự nhận
        # diện định dạng thật và gán đúng đuôi khi lưu file.
        url = f"{self.base_url}{file_id}.jpg"
        return self.http.download(url, save_dir, file_id)

    @staticmethod
    def _is_evo5(hero_id: int, skin_index: int) -> bool:
        return (hero_id, skin_index) in EVO5_SKIN_LIST