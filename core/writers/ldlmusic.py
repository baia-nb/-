# -*- coding: utf-8 -*-
"""ldlmusic 音乐文件写入器 / ldlmusic music file writer.

格式:
    头部 "LDLM" + 版本(1byte) + 音符数(4byte) + tempo(4byte) + ppq(4byte)
    每个音符: instrument(1byte) + pitch(1byte) + velocity(1byte) + tick(4byte)
整体用 zlib 压缩后再 base64 编码。
"""
import os
import zlib
import base64
import struct
from ..paths import get_desktop_dir, ensure_dir


MAGIC = b"LDLM"
VERSION = 1

# Minecraft 音色 -> 1 字节 ID 映射 / instrument name to 1-byte id
INSTRUMENT_MAP = {
    "harp": 0,
    "basedrum": 1,
    "bass": 2,
    "snare": 3,
    "hat": 4,
    "guitar": 5,
    "flute": 6,
    "bell": 7,
    "chime": 8,
    "xylophone": 9,
    "iron_xylophone": 10,
    "cow_bell": 11,
    "didgeridoo": 12,
    "bit": 13,
    "banjo": 14,
    "pling": 15,
}


def _instrument_id(name):
    """音色名转 1 字节 ID / instrument name to 1-byte id."""
    if name in INSTRUMENT_MAP:
        return INSTRUMENT_MAP[name]
    # 未知音色用稳定哈希映射到 16..255 / hash unknown instruments to 16..255
    return 16 + (hash(name) & 0xFF) % 240 if name else 0


def write(midi_data, out_path=None, name=None):
    """写入 ldlmusic 音乐文件 / write ldlmusic music file.

    Args:
        midi_data: MidiData 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    fname = (name or "music") + ".ldlmusic"
    notes = midi_data.notes
    tempo = int(getattr(midi_data, "tempo", 500000))
    ppq = int(getattr(midi_data, "ppq", 480))

    # 头部
    header = bytearray()
    header += MAGIC
    header += bytes([VERSION])
    header += struct.pack("<I", len(notes))
    header += struct.pack("<I", tempo & 0xFFFFFFFF)
    header += struct.pack("<I", ppq & 0xFFFFFFFF)

    # 音符载荷
    payload = bytearray()
    for note in notes:
        payload += bytes([_instrument_id(note.instrument) & 0xFF])
        payload += bytes([int(note.pitch) & 0xFF])
        payload += bytes([int(note.velocity) & 0xFF])
        payload += struct.pack("<I", int(note.tick) & 0xFFFFFFFF)

    # zlib 压缩 + base64 编码
    raw = bytes(header) + bytes(payload)
    compressed = zlib.compress(raw)
    encoded = base64.b64encode(compressed)

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        out_path = os.path.join(out_dir, fname)

    with open(out_path, "wb") as f:
        f.write(encoded)
    return out_path
