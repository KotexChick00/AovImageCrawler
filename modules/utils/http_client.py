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

from modules.core.config import DUPLICATE_CHECK


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
    - Bỏ qua nếu URL đã từng tải (theo downloaded_urls.txt) hoặc file đã tồn tại.
    - Ghi persistent log và cập nhật session tracker khi tải thành công.
    """

    def __init__(self, log_dir: str, timeout: int = 10, check_mode: str | None = None) -> None:
        self.log_dir = log_dir
        self.timeout = timeout
        self._check_mode = check_mode or DUPLICATE_CHECK
        if self._check_mode not in ("disk", "url"):
            raise ValueError(f"DUPLICATE_CHECK phải là 'disk' hoặc 'url', không phải {self._check_mode!r}")
        self._log_lock      = threading.Lock()
        self._manifest_lock = threading.Lock()
        self._manifest_path = os.path.join(log_dir, "downloaded_urls.txt")
        self._downloaded_urls: set[str] = (
            self._load_manifest() if self._check_mode == "url" else set()
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def download(
        self, url: str, save_dir: str, file_id: str, quiet_missing: bool = False
    ) -> DownloadStatus:
        """
        Tải url, tự động nhận diện định dạng thực tế (qua Content-Type / magic bytes)
        để gán đuôi file đúng (.jpg/.png/...).

        `quiet_missing=True`: không in dòng "Not found" khi server trả 404
        (dùng cho các lần quét dò B-suffix, nơi phần lớn request đều miss).

        `file_id` KHÔNG kèm đuôi file — đuôi sẽ được xác định sau khi tải về.
        Việc kiểm tra "đã tồn tại" được thực hiện bằng cách tìm mọi file có tên
        `{file_id}.*` trong `save_dir`, bất kể đuôi thật là gì.
        """
        # Chế độ "url": đã từng tải URL này (kể cả khi file đã bị đổi tên / di chuyển)
        if self._check_mode == "url":
            with self._manifest_lock:
                already = url in self._downloaded_urls
            if already:
                print(f"Already downloaded: {url}")
                return "exists"

        # File còn nguyên tên `{file_id}.*` trên đĩa (cả hai chế độ đều kiểm tra bước này)
        existing = self._find_existing(save_dir, file_id)
        if existing is not None:
            if self._check_mode == "url":
                self._remember_url(url)   # lần sau không phụ thuộc tên file nữa
            print(f"Already exists: {existing}")
            return "exists"

        try:
            response = requests.get(url, timeout=self.timeout)
        except Exception as exc:
            print(f"Error downloading {url}: {exc}")
            return "missing"

        if response.status_code != 200:
            if not quiet_missing:
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
        self._remember_url(url)
        self._append_persistent_log(file_path)
        session_tracker.record(file_path)
        return "downloaded"

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _find_existing(save_dir: str, file_id: str) -> str | None:
        """Tìm file `{file_id}.*` đã có trong save_dir, không phụ thuộc đuôi thật."""
        matches = sorted(glob.glob(os.path.join(save_dir, f"{file_id}.*")))
        return matches[0] if matches else None

    def _load_manifest(self) -> set[str]:
        """Đọc danh sách URL đã tải (mỗi dòng một URL)."""
        try:
            with open(self._manifest_path, "r", encoding="utf-8") as f:
                return {line.strip() for line in f if line.strip()}
        except FileNotFoundError:
            return set()

    def _remember_url(self, url: str) -> None:
        """Thêm URL vào manifest (thread-safe, ghi nối tiếp ra file). Chỉ dùng ở chế độ "url"."""
        if self._check_mode != "url":
            return
        with self._manifest_lock:
            if url in self._downloaded_urls:
                return
            self._downloaded_urls.add(url)
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self._manifest_path, "a", encoding="utf-8") as f:
                f.write(f"{url}\n")

    def _append_persistent_log(self, file_path: str) -> None:
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, "download.log")
        with self._log_lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{file_path}\n")