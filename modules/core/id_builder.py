"""
id_builder.py — Các class xây dựng file ID theo từng loại asset.

Mỗi loại asset (Splash / Head / Bust) có quy tắc đặt tên riêng;
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

    @abstractmethod
    def build_filename(self, hero_name: str, hero_id: int, skin_index: int, evo5: bool = False) -> str: ...


class SplashIDBuilder(BaseIDBuilder):
    """
    Splash skin ID: {hero_id}{skin_index:02}[_2]
    Ví dụ:
        hero=196, skin=2        → 19602
        hero=196, skin=2, evo5  → 19602_2
    
    New filename format: Hero_Splash_{HeroName}_{HeroID}_{SkinID}
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        base = f"{hero_id}{skin_index:02}"
        return f"{base}{EVO5_ALT_SUFFIX}" if evo5 else base

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)

    def build_filename(self, hero_name: str, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        evo_suffix = EVO5_ALT_SUFFIX if evo5 else ""
        return f"Hero_Splash_{hero_name}_{hero_id}_{skin_index}{evo_suffix}"

    def build_b_variant(self, hero_id: int, b_suffix: int) -> str:
        """B-suffix variant: {hero_id}00_B{b_suffix}"""
        return f"{hero_id}00_B{b_suffix}"

    def build_b_filename(self, hero_name: str, hero_id: int, skin_index: int, b_suffix: int) -> str:
        return f"Hero_Splash_{hero_name}_{hero_id}_{skin_index}_B{b_suffix}"


class HeadIDBuilder(BaseIDBuilder):
    """
    Head skin ID: 30{hero_id}{skin_index}[_2]head
    Skin index KHÔNG có zero-padding.
    Ví dụ:
        hero=196, skin=0        → 301960head
        hero=196, skin=2        → 301962head
        hero=196, skin=2, evo5  → 301962_2head
    
    New filename format: Hero_Head_{HeroName}_{HeroID}_{SkinID}
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        skin_part = str(skin_index)
        evo_part  = EVO5_ALT_SUFFIX if evo5 else ""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}{HEAD_ICON_REQUIRED_SUFFIX}"

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)

    def build_filename(self, hero_name: str, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        evo_suffix = EVO5_ALT_SUFFIX if evo5 else ""
        return f"Hero_Head_{hero_name}_{hero_id}_{skin_index}{evo_suffix}"

    def build_b_variant(self, hero_id: int, skin_index: int, b_suffix: int) -> str:
        """B-variant: 30{hero_id}{skin_index}head_B{b_suffix} (vd: 301270head_B51)"""
        return f"{self.build(hero_id, skin_index)}_B{b_suffix}"

    def build_b_filename(self, hero_name: str, hero_id: int, skin_index: int, b_suffix: int) -> str:
        return f"Hero_Head_{hero_name}_{hero_id}_{skin_index}_B{b_suffix}"


class BustIDBuilder(BaseIDBuilder):
    """
    Bust skin ID: 30{hero_id}{skin_index}[_2]
    Giống Head nhưng không có suffix 'head'.
    Ví dụ:
        hero=196, skin=2        → 301962
        hero=196, skin=2, evo5  → 301962_2
    
    New filename format: Hero_Bust_{HeroName}_{HeroID}_{SkinID}
    """

    def build(self, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        skin_part = str(skin_index)
        evo_part  = EVO5_ALT_SUFFIX if evo5 else ""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}"

    def build_base(self, hero_id: int) -> str:
        return self.build(hero_id, 0)

    def build_filename(self, hero_name: str, hero_id: int, skin_index: int, evo5: bool = False) -> str:
        evo_suffix = EVO5_ALT_SUFFIX if evo5 else ""
        return f"Hero_Bust_{hero_name}_{hero_id}_{skin_index}{evo_suffix}"

    def build_b_variant(self, hero_id: int, skin_index: int, b_suffix: int) -> str:
        """B-variant: 30{hero_id}{skin_index}_B{b_suffix} (vd: 301270_B51)"""
        return f"{self.build(hero_id, skin_index)}_B{b_suffix}"

    def build_b_filename(self, hero_name: str, hero_id: int, skin_index: int, b_suffix: int) -> str:
        return f"Hero_Bust_{hero_name}_{hero_id}_{skin_index}_B{b_suffix}"

    def build_flowborn(self, hero_id: int, gender: str) -> str:
        """Flowborn bust ID: 30{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}"""
        return f"{HEAD_REQUIRED_PREFIX}{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}"

    def build_flowborn_filename(self, hero_name: str, hero_id: int, gender: str) -> str:
        """Flowborn filename: Hero_Bust_{HeroName}_{HeroID}_{gender}"""
        return f"Hero_Bust_{hero_name}_{hero_id}_{gender}"