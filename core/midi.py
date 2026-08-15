# -*- coding: utf-8 -*-
"""MIDI 解析器 / MIDI parser.

解析标准 MIDI 文件 (Format 0/1), 提取音符事件并转换为 Minecraft 音符方块数据。
参考 Exchange Tool v13.0 的 MIDI 处理逻辑。
"""
import io
import struct

from .model import MidiData, Note


# MIDI 通道 → MC 乐器映射 (channel 9 是标准鼓组)
_CHANNEL_INSTR = {
    0: "harp",
    1: "bass",
    2: "snare",
    3: "hat",
    4: "basedrum",
    9: "drum",  # 鼓组通道, 后续按音高细分
}

# 鼓组 (channel 9) 按音高细分映射
_DRUM_PITCH_MAP = {
    # 低音桶 → basedrum
    35: "basedrum", 36: "basedrum",
    # 军鼓 / 小军鼓
    38: "snare", 40: "snare",
    # 踩镲
    42: "hat", 44: "hat", 46: "hat",
    # 低音底鼓
    41: "basedrum", 43: "basedrum", 45: "basedrum", 47: "basedrum",
}


def _read_varlen(f):
    """读取变长字节 (variable-length quantity) / read MIDI variable-length int.

    每字节低 7 位有效, 最高位 1 表示后续还有字节。
    """
    value = 0
    for _ in range(4):  # varlen 最多 4 字节
        b = f.read(1)
        if not b:
            break
        byte = b[0]
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value


def _u16(f):
    return struct.unpack(">H", f.read(2))[0]


def _u32(f):
    return struct.unpack(">I", f.read(4))[0]


def _read_track(f, track_len):
    """解析单个 MTrk 块 / parse a single MTrk chunk.

    返回 (notes_list, tempo, end_tick)。
    """
    end = f.tell() + track_len
    notes = []
    tempo = None
    abs_tick = 0
    running_status = None  # 运行状态: 上一条状态字节

    while f.tell() < end:
        delta = _read_varlen(f)
        abs_tick += delta

        status_byte = f.read(1)
        if not status_byte:
            break
        status = status_byte[0]

        # 运行状态: 高位为 0 表示复用上一条状态字节
        if not (status & 0x80):
            # 当前字节实际是数据字节, 状态沿用 running_status
            data1 = status
            status = running_status
        else:
            running_status = status
            data1 = f.read(1)[0] if f.tell() < end else 0

        msg_type = status & 0xF0
        channel = status & 0x0F

        if msg_type == 0x80:
            # note_off
            data2 = f.read(1)[0]
            # note_off 不再产生音符 (note_on 时已记录)
            continue
        elif msg_type == 0x90:
            # note_on, velocity=0 等同 note_off
            data2 = f.read(1)[0]
            if data2 == 0:
                continue
            instr = _resolve_instrument(channel, data1)
            notes.append(Note(instrument=instr, pitch=data1, velocity=data2, tick=abs_tick))
        elif msg_type in (0xA0, 0xB0, 0xE0):
            # polyphonic / control / pitch-bend: 跳过 1 字节
            f.read(1)
        elif msg_type == 0xC0 or msg_type == 0xD0:
            # program change / channel pressure: 仅 1 字节数据, 已读取 data1
            continue
        elif status == 0xFF:
            # meta 事件: data1 是 meta 类型, 后跟 varlen 长度 + 数据
            meta_len = _read_varlen(f)
            meta_data = f.read(meta_len)
            if data1 == 0x51 and meta_len >= 3:
                # tempo: 3 字节 microseconds per quarter
                mpq = (meta_data[0] << 16) | (meta_data[1] << 8) | meta_data[2]
                tempo = mpq
            # 0x2F end_of_track 等其它 meta 忽略
        elif msg_type == 0xF0:
            # 系统专属事件: 后续以 varlen 长度 + 数据 (data1 已读)
            sysex_len = _read_varlen(f)
            f.read(sysex_len)
        # 其它未知事件忽略

    return notes, tempo, abs_tick


def _resolve_instrument(channel, note):
    """将 MIDI 通道/音高映射为 MC 乐器 / map channel & note to MC instrument."""
    if channel == 9:
        # 鼓组: 按音高细分, 缺省回退 hat
        return _DRUM_PITCH_MAP.get(note, "hat")
    # 非鼓组: 按通道粗分, 鼓组外默认 harp (按需求简化)
    return _CHANNEL_INSTR.get(channel, "harp")


def read_midi(path) -> MidiData:
    """读取并解析 MIDI 文件 / read and parse a MIDI file.

    支持 Format 0/1, 返回 MidiData。
    失败时抛出 ValueError。
    """
    try:
        with open(path, "rb") as fp:
            data = fp.read()
    except OSError as e:
        raise ValueError(f"无法读取 MIDI 文件: {e}")

    f = io.BytesIO(data)

    # 头部块
    header = f.read(4)
    if header != b"MThd":
        raise ValueError("无效的 MIDI 文件: 缺少 MThd 头")

    header_len = _u32(f)
    fmt = _u16(f)
    ntracks = _u16(f)
    division = _u16(f)
    # 跳过头部剩余字节
    if header_len > 6:
        f.read(header_len - 6)

    if fmt not in (0, 1):
        raise ValueError(f"不支持的 MIDI 格式: {fmt} (仅支持 0/1)")

    # SMPTE 格式 (division 高位为 1) 暂不支持, 仅处理 PPQ
    if division & 0x8000:
        raise ValueError("不支持 SMPTE 时间格式 MIDI (仅支持 PPQ)")

    result = MidiData(ppq=division, tempo=500000)
    total_ticks = 0

    for _ in range(ntracks):
        chunk_id = f.read(4)
        if not chunk_id:
            break
        if chunk_id != b"MTrk":
            # 非 MTrk 块: 读取长度后跳过
            chunk_len = _u32(f)
            f.read(chunk_len)
            continue

        track_len = _u32(f)
        if track_len == 0:
            continue

        # 保存当前位置以便回退 (read_track 不一定读满 track_len)
        start = f.tell()
        notes, tempo, end_tick = _read_track(f, track_len)
        # 确保指针跳到块末 (容错)
        f.seek(start + track_len)

        for n in notes:
            result.add(n)
        if tempo is not None:
            result.tempo = tempo
        if end_tick > total_ticks:
            total_ticks = end_tick

    result.duration = total_ticks
    return result
