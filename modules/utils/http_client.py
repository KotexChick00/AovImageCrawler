"""
http_client.py — HTTP downloader với session tracking thread-safe.

Tách riêng tầng mạng khỏi logic nghiệp vụ giúp dễ mock khi test
và dễ swap transport (aiohttp, httpx…) về sau.
"""

from __future__ import annotations

import os
import threading
from typing import Literal

import requests


# ── Session tracking ──────────────────────────────────────────────────────────

DownloadStatus = Literal["downloaded", "exists", "missing"]


class SessionTracker:
    """Ghi nhận các file mới tải trong phiên hiện tại (thread-safe)."""

    def __init__(self) -> None:
        self._lock      = threading.Lock()
        self._downloads: list[str] = []

    def record(self, file_path: str) -> None:
        with self._lock:
            self._downloads.append(file_path)

    @property
    def downloads(self) -> list[str]:
        with self._lock:
            return list(self._downloads)

    def __len__(self) -> int:
        with self._lock:
            return len(self._downloads)


# ── Singleton tracker (dùng chung toàn app) ───────────────────────────────────
session_tracker = SessionTracker()


# ── HTTP client ───────────────────────────────────────────────────────────────

class HttpClient:
    """
    Tải một file từ URL về đĩa.
    - Bỏ qua nếu file đã tồn tại.
    - Ghi persistent log và cập nhật session tracker khi tải thành công.
    """

    def __init__(self, log_dir: str, timeout: int = 10) -> None:
        self.log_dir = log_dir
        self.timeout = timeout

    # ── Public ────────────────────────────────────────────────────────────────

    def download(self, url: str, save_dir: str, filename: str) -> DownloadStatus:
        """Tải url → save_dir/filename. Trả về trạng thái."""
        file_path = os.path.join(save_dir, filename)

        if os.path.exists(file_path):
            print(f"Already exists: {file_path}")
            return "exists"

        try:
            response = requests.get(url, timeout=self.timeout)
        except Exception as exc:
            print(f"Error downloading {url}: {exc}")
            return "missing"

        if response.status_code != 200:
            print(f"Not found: {url}")
            return "missing"

        os.makedirs(save_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"Downloaded: {file_path}")
        self._append_persistent_log(file_path)
        session_tracker.record(file_path)
        return "downloaded"

    # ── Private ───────────────────────────────────────────────────────────────

    def _append_persistent_log(self, file_path: str) -> None:
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, "download.log")
        with threading.Lock():                     # file-level lock (best-effort)
            with open(log_path, "a") as f:
                f.write(f"{file_path}\n")