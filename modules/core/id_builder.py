"""
id_builder.py — Các class xây dựng file ID theo từng loại asset.

Mỗi loại asset (Splash / Head / Frame) có quy tắc đặt tên riêng;
tách thành các class giúp dễ test, dễ mở rộng khi quy tắc thay đổi.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from modules.core.config import (
    HEAD_REQUIRED_PREFIX,
    HEAD_ICON_REQUIRED_SUFFIX,
    EVO5_ALT_SUFFIX,
    FLOWBORN_UNIQUE_SUFFIX_ID,
)


class BaseIDBuilder(ABC):
    """Giao diện chung cho tất cả ID builder."""

    @abstractmethod
    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str: ...

    @abstractmethod
    def build_base(self, hero_id: int) -> str: ...


class SplashIDBuilder(BaseIDBuilder):
    """
    Splash skin ID: {hero_id}{skin_index:02}[_2]
    Ví dụ:
        hero=196, skin=2        → 19602
        hero=196, skin=2, evo5  → 19602_2
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        base = f"{hero_id}{skin_index:02}"
        return f"{base}{EVO5_ALT_SUFFIX}" if evo5 else base

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)

    def build_b_variant(self, hero_id: int, b_suffix: int) -> str:
        """B-suffix variant: {hero_id}00_B{b_suffix}"""
        return f"{hero_id}00_B{b_suffix}"


class HeadIDBuilder(BaseIDBuilder):
    """
    Head skin ID: 30{hero_id}{skin_index}[_2]head
    Skin index KHÔNG có zero-padding.
    Ví dụ:
        hero=196, skin=0        → 301960head
        hero=196, skin=2        → 301962head
        hero=196, skin=2, evo5  → 301962_2head
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        skin_part = str(skin_index)
        evo_part  = EVO5_ALT_SUFFIX if evo5 else ""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}{HEAD_ICON_REQUIRED_SUFFIX}"

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)


class FrameIDBuilder(BaseIDBuilder):
    """
    Frame skin ID: 30{hero_id}{skin_index}[_2]
    Giống Head nhưng không có suffix 'head'.
    Ví dụ:
        hero=196, skin=2        → 301962
        hero=196, skin=2, evo5  → 301962_2
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        skin_part = str(skin_index)
        evo_part  = EVO5_ALT_SUFFIX if evo5 else ""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}"

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)

    def build_flowborn(self, hero_id: int, gender: str) -> str:
        """Flowborn frame ID: 30{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}"""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}"

    @staticmethod
    def parse_hero_id_from_special(file_id: str) -> int | None:
        """
        Lấy hero_id từ file_id đặc biệt trong SPECIAL_FRAME.
        Quy tắc: bỏ prefix '30', lấy chuỗi số, bỏ chữ số cuối (skin=0).
        Ví dụ: '301270_B51' → '30' bỏ → '1270' → hero_id=127
        """
        import re
        without_prefix = file_id[len(HEAD_REQUIRED_PREFIX):]
        m = re.match(r"(\d+)", without_prefix)
        if not m:
            return None
        digits = m.group(1)
        if len(digits) < 2:
            return None
        return int(digits[:-1])