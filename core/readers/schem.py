# -*- coding: utf-8 -*-
"""Sponge Schem 格式读取器 / Sponge .schem (v2/v3) reader.

NBT (gzip, 大端)。
- Version (int): 2 或 3
- Width / Height / Length (short)
- Palette (compound): name -> index
- BlockData (byte[]): varint 编码的 palette 索引序列
- (v3) DataVersion (int)

方块按 YZX 顺序: index = (y * Length + z) * Width + x。
参考 Exchange Tool v13.0。
"""
from ..model import Structure, Block
from ..nbt import parse, to_plain, Tag


def _read_varint(data: bytes, pos: int):
    """读取无符号 VarInt (LEB128), 返回 (value, new_pos)。"""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


def read_schem(path) -> Structure:
    """读取 Sponge .schem 建筑文件 / read sponge schem file."""
    with open(path, "rb") as f:
        data = f.read()
    plain = to_plain(parse(data, little_endian=False, compressed=True))
    st = Structure(format="schem")
    if not isinstance(plain, dict):
        return st

    width = int(plain.get("Width", 0))
    height = int(plain.get("Height", 0))
    length = int(plain.get("Length", 0))
    st.size = (width, height, length)

    palette_tag = plain.get("Palette") or {}
    name_by_idx = {}
    if isinstance(palette_tag, dict):
        for name, idx in palette_tag.items():
            name_by_idx[int(idx)] = name
    palette = [None] * (max(name_by_idx) + 1 if name_by_idx else 0)
    for idx, name in name_by_idx.items():
        palette[idx] = Block(name=name, states={})
    st.palette = [b for b in palette if b is not None]

    block_data = plain.get("BlockData") or []
    if isinstance(block_data, list):
        bd = bytes((b & 0xFF) for b in block_data)
    elif isinstance(block_data, (bytes, bytearray)):
        bd = bytes(block_data)
    else:
        bd = b""

    total = width * height * length
    pos = 0
    indices = []
    for _ in range(total):
        if pos >= len(bd):
            break
        val, pos = _read_varint(bd, pos)
        indices.append(val)

    # index = (y * Length + z) * Width + x  (YZX 顺序)
    for y in range(height):
        for z in range(length):
            base = (y * length + z) * width
            for x in range(width):
                i = base + x
                if i >= len(indices):
                    continue
                idx = indices[i]
                if idx < 0 or idx >= len(palette) or palette[idx] is None:
                    continue
                b = palette[idx]
                if b.name == "minecraft:air":
                    continue
                st.add(Block(name=b.name, states=dict(b.states), data=0,
                             nbt_data={"pos": (x, y, z)}))
    return st
