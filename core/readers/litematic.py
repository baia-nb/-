# -*- coding: utf-8 -*-
"""Litematic 格式读取器 / Litematica (.litematic) reader.

Litematica 是 Java 版 Mod 的建筑格式: NBT (gzip 压缩, 大端)。
- Regions.<name>.BlockStatePalette  方块调色板 (Name + Properties)
- Regions.<name>.BlockStates        打包的 long 数组
- Regions.<name>.Size / Position    结构尺寸 (可能为负) 与原点

位打包: 位宽 bits = max(2, ceil(log2(palette_size))), 与 1.13+ chunk 一致,
LSB 优先, 一个方块索引可跨两个 long。litematica 总是把 minecraft:air 分配为 0。
索引顺序 YZX: index = (y * sizeZ + z) * sizeX + x。
参考 Exchange Tool v13.0。
"""
from ..model import Structure, Block
from ..nbt import parse, to_plain, Tag


def _bits_for_palette(n: int) -> int:
    """计算每个方块所需的位数 (litematica 最小 2 位)。"""
    if n <= 1:
        return 1
    return max(2, (n - 1).bit_length())


def _unpack_long_array(longs, total: int, bits: int):
    """解包 litematica 的位打包 long 数组为方块索引列表。"""
    mask = (1 << bits) - 1
    out = [0] * total
    n = len(longs)
    for i in range(total):
        start = i * bits
        li = start >> 6          # start // 64
        if li >= n:
            break
        off = start & 63          # start % 64
        u = longs[li] & 0xFFFFFFFFFFFFFFFF  # 转无符号 (nbt 读出为有符号)
        if off + bits <= 64:
            out[i] = (u >> off) & mask
        elif li + 1 < n:
            u2 = longs[li + 1] & 0xFFFFFFFFFFFFFFFF
            out[i] = ((u >> off) | (u2 << (64 - off))) & mask
        else:
            out[i] = (u >> off) & mask
    return out


def read_litematic(path) -> Structure:
    """读取 .litematic 建筑文件 / read litematica structure file."""
    with open(path, "rb") as f:
        data = f.read()
    plain = to_plain(parse(data, little_endian=False, compressed=True))
    st = Structure(format="litematic")
    if not isinstance(plain, dict):
        return st

    regions = plain.get("Regions") or {}
    if not isinstance(regions, dict):
        return st

    first = True
    for rname, region in regions.items():
        if not isinstance(region, dict):
            continue
        size_tag = region.get("Size") or {}
        sx = abs(int(size_tag.get("x", 0)))
        sy = abs(int(size_tag.get("y", 0)))
        sz = abs(int(size_tag.get("z", 0)))
        pos_tag = region.get("Position") or {}
        ox = int(pos_tag.get("x", 0))
        oy = int(pos_tag.get("y", 0))
        oz = int(pos_tag.get("z", 0))

        palette_raw = region.get("BlockStatePalette") or []
        palette = []
        for entry in palette_raw:
            if not isinstance(entry, dict):
                continue
            name = entry.get("Name", "minecraft:air")
            props = entry.get("Properties") or {}
            palette.append(Block(name=name, states=dict(props) if isinstance(props, dict) else {}))
        st.palette.extend(palette)

        longs = region.get("BlockStates") or []
        if not isinstance(longs, list):
            longs = []
        total = sx * sy * sz
        bits = _bits_for_palette(len(palette))
        indices = _unpack_long_array(longs, total, bits)

        # index = (y * sizeZ + z) * sizeX + x
        for y in range(sy):
            base_y = y * sz
            for z in range(sz):
                base_z = (base_y + z) * sx
                for x in range(sx):
                    i = base_z + x
                    if i >= len(indices):
                        continue
                    idx = indices[i]
                    if idx < 0 or idx >= len(palette):
                        continue
                    b = palette[idx]
                    if b.name == "minecraft:air":
                        continue
                    st.add(Block(name=b.name, states=dict(b.states), data=0,
                                 nbt_data={"pos": (x, y, z), "region": rname}))

        if first:
            st.size = (sx, sy, sz)
            st.origin = (ox, oy, oz)
            first = False
    return st
