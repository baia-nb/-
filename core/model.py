# -*- coding: utf-8 -*-
"""数据模型 / data models.

统一存储解析后的结构和音符数据, 供各插件使用。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Block:
    """方块 / block."""
    name: str          # 如 "minecraft:stone"
    states: Dict = field(default_factory=dict)
    data: int = 0      # 基岩版特殊值
    nbt_data: Optional[dict] = None  # 命令方块 NBT 等


@dataclass
class Structure:
    """建筑结构 / structure."""
    blocks: List[Block] = field(default_factory=list)
    palette: List[Block] = field(default_factory=list)
    size: tuple = (0, 0, 0)
    offset: tuple = (0, 0, 0)
    origin: tuple = (0, 0, 0)
    format: str = ""

    def add(self, block):
        self.blocks.append(block)

    def __len__(self):
        return len(self.blocks)


@dataclass
class Note:
    """音符 / note."""
    instrument: str = "harp"
    pitch: int = 0
    velocity: int = 100
    tick: int = 0


@dataclass
class MidiData:
    """MIDI 数据 / midi data."""
    notes: List[Note] = field(default_factory=list)
    tempo: int = 500000  # 微秒/拍
    ppq: int = 480       # pulses per quarter
    duration: int = 0

    def add(self, note):
        self.notes.append(note)


@dataclass
class NbsData:
    """NBS (Note Block Studio) 数据 / nbs data."""
    notes: List[Note] = field(default_factory=list)
    version: int = 0
    length: int = 0
    tempo: int = 10  # ticks/second

    def add(self, note):
        self.notes.append(note)
