"""
renamer.py — Đổi tên file đã tải từ ID gốc sang tên đọc được.

    301270head_B51.jpg  →  Hero_Head_AzzenKa_127_0_B51.jpg

Module này ĐỘC LẬP với tầng tải: không gọi mạng, chỉ đọc các thư mục
splash/ head/ bust/ rồi đổi tên tại chỗ. Cách đặt tên dùng lại
build_filename() của id_builder nên chỉ có một nguồn quy tắc đặt tên.

An toàn khi chạy lại nhiều lần:
  - File đã có tên đẹp (không khớp dạng ID gốc) được bỏ qua.
  - Không bao giờ ghi đè: nếu tên đích đã tồn tại thì báo xung đột và giữ nguyên.
  - Hero không có trong hero.json thì giữ nguyên file và báo lại.
  - Đuôi file được giữ nguyên (.jpg/.png/...).

Chạy:  python -m modules.utils.renamer [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from typing import Callable

from modules.core.config import (
    BUST_DIR, HEAD_DIR, SPLASH_DIR,
    HEAD_REQUIRED_PREFIX,
    FLOWBORN_SPECIAL_HERO_ID,
    FLOWBORN_UNIQUE_SUFFIX_ID,
    FLOWBORN_GENDER_SUFFIX_BUST,
    HERO_NAME_MAP,
)
from modules.core.id_builder import BustIDBuilder, HeadIDBuilder, SplashIDBuilder

# parser: (hero_id, hero_name, stem) -> tên mới (không đuôi) hoặc None nếu stem không phải ID gốc
Parser = Callable[[int, str, str], "str | None"]


# ── Parsers ───────────────────────────────────────────────────────────────────
# Thư mục cha đã cho biết hero_id, nên chỉ cần bóc phần đứng sau hero_id
# → không bị nhập nhằng giữa hero_id và skin_index.

_splash = SplashIDBuilder()
_head   = HeadIDBuilder()
_bust   = BustIDBuilder()


def _parse_splash(hero_id: int, name: str, stem: str) -> str | None:
    prefix = str(hero_id)
    if not stem.startswith(prefix):
        return None
    rest = stem[len(prefix):]

    m = re.fullmatch(r"(\d{2})(_2)?", rest)                 # {hero}{skin:02}[_2]
    if m:
        return _splash.build_filename(name, hero_id, int(m.group(1)), bool(m.group(2)))
    m = re.fullmatch(r"00_B(\d+)", rest)                    # {hero}00_B{n}
    if m:
        return _splash.build_b_filename(name, hero_id, 0, int(m.group(1)))
    return None


def _parse_head(hero_id: int, name: str, stem: str) -> str | None:
    prefix = f"{HEAD_REQUIRED_PREFIX}{hero_id}"
    if not stem.startswith(prefix):
        return None
    rest = stem[len(prefix):]

    m = re.fullmatch(r"(\d+)(_2)?head(?:_B(\d+))?", rest)   # {skin}[_2]head[_B{n}]
    if not m:
        return None
    skin, evo, b = int(m.group(1)), bool(m.group(2)), m.group(3)
    if b is not None:
        return _head.build_b_filename(name, hero_id, skin, int(b))
    return _head.build_filename(name, hero_id, skin, evo)


def _parse_bust(hero_id: int, name: str, stem: str) -> str | None:
    prefix = f"{HEAD_REQUIRED_PREFIX}{hero_id}"
    if not stem.startswith(prefix):
        return None
    rest = stem[len(prefix):]

    if hero_id in FLOWBORN_SPECIAL_HERO_ID:                 # {00}{m|f}
        genders = "".join(FLOWBORN_GENDER_SUFFIX_BUST)
        m = re.fullmatch(rf"{FLOWBORN_UNIQUE_SUFFIX_ID}([{genders}])", rest)
        if m:
            return _bust.build_flowborn_filename(name, hero_id, m.group(1))

    m = re.fullmatch(r"(\d+)(_2)?(?:_B(\d+))?", rest)       # {skin}[_2][_B{n}]
    if not m:
        return None
    skin, evo, b = int(m.group(1)), bool(m.group(2)), m.group(3)
    if b is not None:
        return _bust.build_b_filename(name, hero_id, skin, int(b))
    return _bust.build_filename(name, hero_id, skin, evo)


# ── Report ────────────────────────────────────────────────────────────────────

@dataclass
class RenameReport:
    renamed:      list[tuple[str, str]] = field(default_factory=list)
    skipped:      int = 0                                        # đã có tên đẹp / không nhận diện
    conflicts:    list[tuple[str, str]] = field(default_factory=list)
    unknown_hero: set[int] = field(default_factory=set)


# ── Renamer ───────────────────────────────────────────────────────────────────

class AssetRenamer:
    def __init__(
        self,
        hero_names: dict[int, str] | None = None,
        splash_dir: str = SPLASH_DIR,
        head_dir: str = HEAD_DIR,
        bust_dir: str = BUST_DIR,
    ) -> None:
        self._names = HERO_NAME_MAP if hero_names is None else hero_names
        self._targets: list[tuple[str, Parser]] = [
            (splash_dir, _parse_splash),
            (head_dir,   _parse_head),
            (bust_dir,   _parse_bust),
        ]

    def rename_all(self, dry_run: bool = False) -> RenameReport:
        report = RenameReport()
        for root, parser in self._targets:
            self._rename_root(root, parser, report, dry_run)
        return report

    def _rename_root(self, root: str, parser: Parser, report: RenameReport, dry_run: bool) -> None:
        if not os.path.isdir(root):
            return
        for hero_folder in sorted(os.listdir(root)):
            hero_path = os.path.join(root, hero_folder)
            if not (hero_folder.isdigit() and os.path.isdir(hero_path)):
                continue
            hero_id = int(hero_folder)
            name = self._names.get(hero_id)

            for fname in sorted(os.listdir(hero_path)):
                stem, ext = os.path.splitext(fname)
                new_stem = parser(hero_id, name or "?", stem)
                if new_stem is None:
                    report.skipped += 1
                    continue
                if name is None:
                    report.unknown_hero.add(hero_id)
                    continue

                old_path = os.path.join(hero_path, fname)
                new_path = os.path.join(hero_path, f"{new_stem}{ext}")
                if os.path.exists(new_path):
                    report.conflicts.append((old_path, new_path))
                    continue
                if not dry_run:
                    os.rename(old_path, new_path)
                report.renamed.append((old_path, new_path))


# ── CLI ───────────────────────────────────────────────────────────────────────

def print_report(report: RenameReport, dry_run: bool = False) -> None:
    label = "Sẽ đổi" if dry_run else "Đã đổi"
    for old, new in report.renamed:
        print(f"{os.path.basename(old)}  →  {os.path.basename(new)}")
    for old, new in report.conflicts:
        print(f"[Xung đột] {old}  →  {os.path.basename(new)} đã tồn tại, giữ nguyên")
    if report.unknown_hero:
        print(f"[Thiếu tên] hero không có trong hero.json: {sorted(report.unknown_hero)}")
    print(f"\n{label} {len(report.renamed)} file, bỏ qua {report.skipped}, "
          f"xung đột {len(report.conflicts)}.")


def run(dry_run: bool = False) -> RenameReport | None:
    if not HERO_NAME_MAP:
        print("Không có dữ liệu hero (hero.json) → không thể đổi tên.")
        return None
    report = AssetRenamer().rename_all(dry_run=dry_run)
    print_report(report, dry_run)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Đổi tên file đã tải sang tên đọc được.")
    parser.add_argument("--dry-run", action="store_true", help="chỉ in kế hoạch, không đổi tên")
    run(dry_run=parser.parse_args().dry_run)


if __name__ == "__main__":
    main()