# -*- coding: utf-8 -*-
"""IBI 加密命令方块包写入器 / IBI encrypted command block pack writer.

IBI 是 Exchange Tool 自定义的加密命令方块包格式:
    魔数 "IBImport" + 版本(1byte) + 文件名(UTF-8 length-prefixed)
    + 数据长度(4byte) + 加密数据(命令方块 NBT 的 JSON 序列化)

简化实现: 用文件名 SHA1 前缀作为密钥做 XOR 加密。
"""
import os
import json
import hashlib
import struct
from ..paths import get_desktop_dir, ensure_dir


MAGIC = b"IBImport"
VERSION = 1


def _xor_encrypt(data, key):
    """XOR 加密 / XOR cipher."""
    if not key:
        return bytes(data)
    klen = len(key)
    return bytes(b ^ key[i % klen] for i, b in enumerate(data))


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


def _build_command_nbt(command):
    """构建命令方块 NBT (JSON 表示) / build command block NBT as JSON."""
    return {
        "command": command,
        "auto": 1,
        "CustomName": "",
        "conditionalMode": 0,
    }


def write(structure, out_path=None, name=None):
    """写入 IBI 加密命令方块包 / write IBI encrypted command block pack.

    Args:
        structure: Structure 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    fname = (name or "structure") + ".ibi"
    size = getattr(structure, "size", (0, 0, 0))

    # 收集所有方块为 setblock 指令并转为命令方块 NBT
    nbt_list = []
    for idx, block in enumerate(structure.blocks):
        x, y, z = _get_pos(block, idx, size)
        states_str = _format_states(getattr(block, "states", {}))
        cmd = f"setblock ~{x} ~{y} ~{z} {block.name}{states_str}"
        nbt_list.append(_build_command_nbt(cmd))

    payload = json.dumps(nbt_list, ensure_ascii=False).encode("utf-8")

    # 用文件名 SHA1 前缀作为 XOR 密钥
    key = hashlib.sha1(fname.encode("utf-8")).digest()[:8]
    encrypted = _xor_encrypt(payload, key)

    # 组装文件: 魔数 + 版本 + 文件名(长度前缀) + 数据长度 + 加密数据
    name_bytes = fname.encode("utf-8")
    out = bytearray()
    out += MAGIC
    out += bytes([VERSION])
    out += struct.pack("<H", len(name_bytes))
    out += name_bytes
    out += struct.pack("<I", len(encrypted))
    out += encrypted

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        out_path = os.path.join(out_dir, fname)

    with open(out_path, "wb") as f:
        f.write(bytes(out))
    return out_path
