"""
logger.py — Ghi session log sau khi hoàn thành tải.
"""

from __future__ import annotations

import os
from datetime import datetime

from modules.utils.http_client import session_tracker


class SessionLogger:
    """Ghi tóm tắt phiên tải vào file log có đánh dấu thời gian."""

    def __init__(self, log_dir: str) -> None:
        self.log_dir = log_dir

    def write(self, finished_at: datetime | None = None) -> None:
        finished_at = finished_at or datetime.now()
        os.makedirs(self.log_dir, exist_ok=True)

        timestamp    = finished_at.strftime("%Y%m%d%H%M%S")
        log_filename = os.path.join(self.log_dir, f"{timestamp}.log")
        downloads    = session_tracker.downloads

        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(f"=== Session log — {finished_at.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Total new files downloaded: {len(downloads)}\n\n")
            for path in sorted(downloads):
                f.write(f"{os.path.basename(path)}\n")

        print(f"\nSession log saved: {log_filename} ({len(downloads)} new file(s))")