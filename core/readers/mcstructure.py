# -*- coding: utf-8 -*-
"""MCStructure 格式读取器 / Bedrock .mcstructure reader.

基岩版原生结构文件: NBT (小端, 通常未压缩, 也可能是 gzip)。
- format_version, size[x,y,z]
- structure.block_indices  [[layer0...], [layer1...]]  (索引, -1 = 空/structure void)
- structure.palette.default.block_palette  [{name, states, version}]
- structure_origin / structure_world_origin

索引顺序 ZYX: index = sizeZ*sizeY*X + sizeZ*Y + Z。
参考 Exchange Tool v13.0。
"""
from ..model import Structure, Block
from ..nbt import parse, to_plain, Tag


def _try_parse(data: bytes):
    """mcstructure 可能未压缩或 gzip; 依次尝试小端/大端 + 压缩/未压缩。"""
    last = {}
    for le, comp in [(True, False), (True, True), (False, False), (False, True)]:
        try:
            plain = to_plain(parse(data, little_endian=le, compressed=comp))
        except Exception:
            continue
        if isinstance(plain, dict) and ("structure" in plain or "format_version" in plain or "size" in plain):
            return plain
        if isinstance(plain, dict) and plain:
            last = plain
    return last


def read_mcstructure(path) -> Structure:
    """读取基岩版 .mcstructure 建筑文件 / read bedrock mcstructure file."""
    with open(path, "rb") as f:
        data = f.read()
    plain = _try_parse(data)
    st = Structure(format="mcstructure")
    if not isinstance(plain, dict):
        return st

    size = plain.get("size") or [0, 0, 0]
    sx, sy, sz = int(size[0]), int(size[1]), int(size[2])
    st.size = (sx, sy, sz)

    origin = plain.get("structure_origin") or plain.get("structure_world_origin") or [0, 0, 0]
    st.origin = (int(origin[0]), int(origin[1]), int(origin[2]))

    structure = plain.get("structure") or {}
    palette_root = structure.get("palette") or {}
    default = palette_root.get("default") or {}
    block_palette = default.get("block_palette") or []
    palette = []
    for entry in block_palette:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "minecraft:air")
        states = entry.get("states") or {}
        palette.append(Block(name=name, states=dict(states) if isinstance(states, dict) else {}))
    st.palette = palette

    block_indices = structure.get("block_indices") or []
    layer0 = block_indices[0] if len(block_indices) > 0 else []
    if not isinstance(layer0, list):
        layer0 = []

    # index = sizeZ*sizeY*X + sizeZ*Y + Z  (ZYX 顺序)
    for x in range(sx):
        base_x = sz * sy * x
        for y in range(sy):
            base_y = base_x + sz * y
            for z in range(sz):
                i = base_y + z
                if i >= len(layer0):
                    continue
                idx = layer0[i]
                if idx is None or idx == -1:
                    continue
                if idx < 0 or idx >= len(palette):
                    continue
                b = palette[idx]
                if b.name == "minecraft:air":
                    continue
                st.add(Block(name=b.name, states=dict(b.states), data=0,
                             nbt_data={"pos": (x, y, z)}))
    return st
