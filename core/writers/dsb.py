# -*- coding: utf-8 -*-
"""DSB 结构文件写入器 / DSB structure file writer.

DSB 是简化的命令方块结构文件:
    魔数 "DSBv1" + 版本(1byte) + 方块数(4byte)
    + 每个方块 (x, y, z, block_name, data, nbt_json)

强制连锁命令方块模式: 所有方块载体使用 chain_command_block,
原始方块通过 Command 字段中的 setblock 指令还原。
"""
import os
import json
import struct
from ..paths import get_desktop_dir, ensure_dir


MAGIC = b"DSBv1"
VERSION = 1
CARRIER_BLOCK = "chain_command_block"


def _format_states(states):
    if not states:
        return ""
    parts = [f"{k}={v}" for k, v in states.items()]
    return "[" + ",".join(parts) + "]"


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
    """写入 DSB 结构文件 / write DSB structure file.

    Args:
        structure: Structure 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    fname = (name or "structure") + ".dsb"
    size = getattr(structure, "size", (0, 0, 0))
    blocks = structure.blocks

    out = bytearray()
    out += MAGIC
    out += bytes([VERSION])
    out += struct.pack("<I", len(blocks))

    for idx, block in enumerate(blocks):
        x, y, z = _get_pos(block, idx, size)
        states_str = _format_states(getattr(block, "states", {}))
        # 原始方块的 setblock 指令, 存入命令方块 NBT
        cmd = f"setblock ~{x} ~{y} ~{z} {block.name}{states_str}"
        nbt = dict(getattr(block, "nbt_data", None) or {})
        nbt.setdefault("Command", cmd)
        nbt.setdefault("auto", 1)
        nbt.setdefault("CustomName", "")
        nbt.setdefault("conditionalMode", 0)
        nbt_json = json.dumps(nbt, ensure_ascii=False)

        name_bytes = CARRIER_BLOCK.encode("utf-8")
        nbt_bytes = nbt_json.encode("utf-8")
        out += struct.pack("<iii", int(x), int(y), int(z))
        out += struct.pack("<H", len(name_bytes))
        out += name_bytes
        out += struct.pack("<i", int(getattr(block, "data", 0)))
        out += struct.pack("<I", len(nbt_bytes))
        out += nbt_bytes

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        out_path = os.path.join(out_dir, fname)

    with open(out_path, "wb") as f:
        f.write(bytes(out))
    return out_path
