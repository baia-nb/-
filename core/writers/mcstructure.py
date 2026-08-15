# -*- coding: utf-8 -*-
"""MCStructure 写入器 / MCStructure writer (Bedrock Edition).

生成基岩版 .mcstructure 文件 (NBT 小端格式, 不压缩)。
"""
import os
import struct
from ..paths import get_desktop_dir, ensure_dir
from ..nbt import (
    TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE,
    TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY,
    TAG_LONG_ARRAY,
)


# 基岩版方块版本号 (1.20.x) / bedrock block version
BLOCK_VERSION = 17959412


# ------------------------------------------------------------------
# NBT 小端序列化 / little-endian NBT serialization
# ------------------------------------------------------------------
def _write_string(s, little_endian=True):
    fmt = "<H" if little_endian else ">H"
    data = s.encode("utf-8")
    return struct.pack(fmt, len(data)) + data


def _write_payload(value, tag_type, little_endian=True):
    le = little_endian
    out = bytearray()
    if tag_type == TAG_BYTE:
        out += struct.pack("<b" if le else ">b", int(value))
    elif tag_type == TAG_SHORT:
        out += struct.pack("<h" if le else ">h", int(value))
    elif tag_type == TAG_INT:
        out += struct.pack("<i" if le else ">i", int(value))
    elif tag_type == TAG_LONG:
        out += struct.pack("<q" if le else ">q", int(value))
    elif tag_type == TAG_FLOAT:
        out += struct.pack("<f" if le else ">f", float(value))
    elif tag_type == TAG_DOUBLE:
        out += struct.pack("<d" if le else ">d", float(value))
    elif tag_type == TAG_BYTE_ARRAY:
        out += struct.pack("<i" if le else ">i", len(value))
        for v in value:
            out += struct.pack("<b" if le else ">b", int(v))
    elif tag_type == TAG_STRING:
        out += _write_string(str(value), le)
    elif tag_type == TAG_INT_ARRAY:
        out += struct.pack("<i" if le else ">i", len(value))
        for v in value:
            out += struct.pack("<i" if le else ">i", int(v))
    elif tag_type == TAG_LONG_ARRAY:
        out += struct.pack("<i" if le else ">i", len(value))
        for v in value:
            out += struct.pack("<q" if le else ">q", int(v))
    else:
        raise ValueError(f"不支持的 tag 类型 / unsupported tag type: {tag_type}")
    return bytes(out)


def _infer_tag_type(value):
    if isinstance(value, bool):
        return TAG_BYTE
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, float):
        return TAG_DOUBLE
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, dict):
        return TAG_COMPOUND
    if isinstance(value, (list, tuple)):
        return TAG_LIST
    raise ValueError(f"无法推断 tag 类型 / cannot infer tag type for {type(value)}")


def _write_value(value, tag_type, little_endian=True):
    le = little_endian
    out = bytearray()
    if tag_type == TAG_LIST:
        child_type = _infer_tag_type(value[0]) if value else TAG_END
        out += bytes([child_type])
        out += struct.pack("<i" if le else ">i", len(value))
        for item in value:
            out += _write_value(item, child_type, le)
    elif tag_type == TAG_COMPOUND:
        for k, v in value.items():
            out += _write_named(k, v, None, le)
        out += bytes([TAG_END])
    else:
        out += _write_payload(value, tag_type, le)
    return bytes(out)


def _write_named(name, value, tag_type=None, little_endian=True):
    if tag_type is None:
        tag_type = _infer_tag_type(value)
    out = bytearray()
    out += bytes([tag_type])
    out += _write_string(name, little_endian)
    out += _write_value(value, tag_type, little_endian)
    return bytes(out)


# ------------------------------------------------------------------
# 结构辅助 / structure helpers
# ------------------------------------------------------------------
def _block_key(block):
    return (
        block.name,
        tuple(sorted(getattr(block, "states", {}).items())),
        getattr(block, "data", 0),
    )


def _get_pos(block, idx, size):
    pos = getattr(block, "pos", None)
    if pos is not None:
        return pos
    sx, sy, sz = size if size else (1, 1, 1)
    if sx <= 0 or sz <= 0:
        return (0, 0, 0)
    y = idx // (sx * sz)
    rem = idx % (sx * sz)
    z = rem // sx
    x = rem % sx
    return (x, y, z)


def write(structure, out_path=None, name=None):
    """写入基岩版 .mcstructure 文件 / write Bedrock .mcstructure file.

    Args:
        structure: Structure 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    fname = (name or "structure") + ".mcstructure"
    size = getattr(structure, "size", (0, 0, 0))
    sx, sy, sz = size if size else (0, 0, 0)
    sx, sy, sz = max(1, int(sx)), max(1, int(sy)), max(1, int(sz))
    blocks = structure.blocks

    # 构建调色板 / build block palette
    palette = []
    palette_index = {}
    for block in blocks:
        k = _block_key(block)
        if k not in palette_index:
            palette_index[k] = len(palette)
            palette.append(block)

    # 构建 3D 网格 (YZX 顺序: index = x + sx * (z + sz * y))
    total = sx * sy * sz
    grid = [-1] * total
    block_position_data = {}
    for idx, block in enumerate(blocks):
        x, y, z = _get_pos(block, idx, size)
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            cell_idx = x + sx * (z + sz * y)
            pi = palette_index[_block_key(block)]
            grid[cell_idx] = pi
            pos_data = {"block_palette_index": pi}
            nbt = getattr(block, "nbt_data", None)
            if nbt:
                pos_data["block_entity_data"] = nbt
            block_position_data[str(cell_idx)] = pos_data

    # 调色板 NBT
    block_palette_nbt = []
    for block in palette:
        states = dict(getattr(block, "states", {}))
        block_palette_nbt.append({
            "name": block.name,
            "states": states,
            "version": BLOCK_VERSION,
        })

    root = {
        "format_version": 1,
        "size": [sx, sy, sz],
        "structure-world-type": "structure",
        "structure_origin": [0, 0, 0],
        "structure": {
            "block_indices": [grid, [-1] * total],
            "entities": [],
            "palette": {
                "default": {
                    "block_palette": block_palette_nbt,
                    "block_position_data": block_position_data,
                }
            }
        }
    }

    out = bytearray()
    out += _write_named("", root, TAG_COMPOUND, True)

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        out_path = os.path.join(out_dir, fname)

    with open(out_path, "wb") as f:
        f.write(bytes(out))
    return out_path
