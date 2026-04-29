"""
miss_counter.py — Thread-safe consecutive-miss counter.

Dừng vòng lặp skin khi server trả về N lần 404 liên tiếp,
tránh lãng phí băng thông với các hero không có nhiều skin.
"""

from __future__ import annotations
import threading


class MissCounter:
    """Thread-safe counter theo dõi số lần miss liên tiếp cho một hero."""

    def __init__(self, limit: int) -> None:
        self._lock  = threading.Lock()
        self._count = 0
        self.limit  = limit
        self.stopped = False

    # ── Public API ────────────────────────────────────────────────────────────

    def hit(self) -> None:
        """File tìm thấy — reset streak."""
        with self._lock:
            self._count = 0

    def miss(self) -> bool:
        """File không tìm thấy — tăng streak.
        Trả về True nếu đã đạt giới hạn và counter bị dừng."""
        with self._lock:
            self._count += 1
            if self._count >= self.limit:
                self.stopped = True
            return self.stopped

    def reset(self) -> None:
        """Reset hoàn toàn (dùng khi tái sử dụng counter)."""
        with self._lock:
            self._count  = 0
            self.stopped = False