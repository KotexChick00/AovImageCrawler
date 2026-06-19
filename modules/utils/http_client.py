"""
http_client.py — HTTP downloader với session tracking thread-safe.

Tách riêng tầng mạng khỏi logic nghiệp vụ giúp dễ mock khi test
và dễ swap transport (aiohttp, httpx…) về sau.
"""

from __future__ import annotations

import glob
import mimetypes
import os
import threading
from typing import Literal

import requests


# ── Mime / extension detection ────────────────────────────────────────────────

# mimetypes.guess_extension() trả về kết quả không ổn định giữa các hệ điều hành
# (vd: image/jpeg → ".jpe" trên một số máy). Map thủ công cho các định dạng ảnh
# phổ biến để đảm bảo đuôi file luôn nhất quán.
_MIME_EXT_MAP: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg":  ".jpg",
    "image/png":  ".png",
    "image/gif":  ".gif",
    "image/webp": ".webp",
    "image/bmp":  ".bmp",
}

# Magic bytes dùng làm fallback khi header Content-Type thiếu hoặc không đáng tin.
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"BM", ".bmp"),
]


def _detect_extension(content: bytes, content_type: str | None, fallback: str = ".jpg") -> str:
    """
    Xác định đuôi file thực tế.

    Ưu tiên đọc magic bytes của nội dung trả về, vì đây chính là nguồn gốc của
    vấn đề "mime không khớp": server có thể gắn Content-Type sai (vd: trả về
    .png nhưng vẫn báo image/jpeg). Content-Type header chỉ dùng làm fallback
    khi không nhận diện được qua magic bytes.
    """
    # WEBP cần kiểm tra container RIFF + chuỗi "WEBP" ở offset 8
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"

    for signature, ext in _MAGIC_SIGNATURES:
        if content.startswith(signature):
            return ext

    if content_type:
        mime = content_type.split(";")[0].strip().lower()
        if mime in _MIME_EXT_MAP:
            return _MIME_EXT_MAP[mime]
        guessed = mimetypes.guess_extension(mime)
        if guessed:
            return guessed

    return fallback


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

    def download(self, url: str, save_dir: str, file_id: str) -> DownloadStatus:
        """
        Tải url, tự động nhận diện định dạng thực tế (qua Content-Type / magic bytes)
        để gán đuôi file đúng (.jpg/.png/...).

        `file_id` KHÔNG kèm đuôi file — đuôi sẽ được xác định sau khi tải về.
        Việc kiểm tra "đã tồn tại" được thực hiện bằng cách tìm mọi file có tên
        `{file_id}.*` trong `save_dir`, bất kể đuôi thật là gì.
        """
        existing = self._find_existing(save_dir, file_id)
        if existing is not None:
            print(f"Already exists: {existing}")
            return "exists"

        try:
            response = requests.get(url, timeout=self.timeout)
        except Exception as exc:
            print(f"Error downloading {url}: {exc}")
            return "missing"

        if response.status_code != 200:
            print(f"Not found: {url}")
            return "missing"

        ext = _detect_extension(
            response.content,
            response.headers.get("Content-Type"),
        )
        file_path = os.path.join(save_dir, f"{file_id}{ext}")

        os.makedirs(save_dir, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"Downloaded: {file_path}")
        self._append_persistent_log(file_path)
        session_tracker.record(file_path)
        return "downloaded"

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _find_existing(save_dir: str, file_id: str) -> str | None:
        """Tìm file `{file_id}.*` đã có trong save_dir, không phụ thuộc đuôi thật."""
        matches = sorted(glob.glob(os.path.join(save_dir, f"{file_id}.*")))
        return matches[0] if matches else None

    def _append_persistent_log(self, file_path: str) -> None:
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, "download.log")
        with threading.Lock():                     # file-level lock (best-effort)
            with open(log_path, "a") as f:
                f.write(f"{file_path}\n")