# -*- coding: utf-8 -*-
"""NBS (Note Block Studio) 解析器 / NBS parser.

解析 Note Block Studio 文件格式 (v0 旧版与新版), 转换为 Minecraft 音符方块数据。
参考 Exchange Tool v13.0 的 NBS 处理逻辑。
"""
import io
import struct

from .model import NbsData, Note


# NBS 乐器索引 → MC 乐器名
NBS_INSTRUMENTS = {
    0: "harp",
    1: "bass",
    2: "snare",
    3: "hat",
    4: "basedrum",
    5: "bell",
    6: "flute",
    7: "chime",
    8: "guitar",
    9: "xylophone",
    10: "iron_xylophone",
    11: "cow_bell",
    12: "didgeridoo",
    13: "bit",
    14: "banjo",
    15: "pling",
}


def _u8(f):
    return struct.unpack("<B", f.read(1))[0]


def _u16(f):
    return struct.unpack("<H", f.read(2))[0]


def _read_string(f):
    """读取 NBS 字符串 (int32 长度 + UTF-8) / read NBS string."""
    (length,) = struct.unpack("<i", f.read(4))
    if length <= 0:
        return ""
    return f.read(length).decode("utf-8", errors="replace")


def _nbs_key_to_pitch(key):
    """NBS key → MC 音高 / convert NBS key to MC note pitch.

    NBS 中 key 范围 0-87, 对应 2 个八度跨度。
    MC 音符方块合法音高范围 0-24。
    简化映射: key - 33 (八度偏移), 越界则取模 25。
    """
    pitch = key - 33
    if pitch < 0 or pitch > 24:
        pitch = key % 25
    if pitch < 0:
        pitch = 0
    if pitch > 24:
        pitch = 24
    return pitch


def read_nbs(path) -> NbsData:
    """读取并解析 NBS 文件 / read and parse a NBS file.

    自动检测 v0 旧版与新版格式, 返回 NbsData。
    失败时抛出 ValueError。
    """
    try:
        with open(path, "rb") as fp:
            data = fp.read()
    except OSError as e:
        raise ValueError(f"无法读取 NBS 文件: {e}")

    if len(data) < 4:
        raise ValueError("NBS 文件过短")

    f = io.BytesIO(data)
    version = 0
    vanilla_block_count = 0

    # 版本检测: 新版以 0 (2B magic) 开头, 后跟 version (1B)
    first_u16 = _u16(f)
    if first_u16 == 0:
        # 新版
        version = _u8(f)
        if version >= 3:
            vanilla_block_count = _u8(f)
        size = _u16(f)
    else:
        # 旧版 v0: first_u16 即为 size
        version = 0
        size = first_u16

    if version not in (0, 1, 2, 3, 4):
        # 未知版本仍按通用流程尝试
        pass

    result = NbsData(version=version, length=size, tempo=10)
    tick = 0
    layer_index = 0

    # 解析音符层 / parse note layers
    # 每层结构: 重复 { jump(2B) } 直到 jump==0 结束当前层; jump>0 推进 tick
    # 每个 tick 下: 重复 { instrument(1B)+key(1B) } 直到 instrument==0 标记结束
    try:
        while True:
            jump = _u16(f)
            if jump == 0:
                # 当前层结束, 切换到下一层
                layer_index += 1
                tick = 0
                # 检测是否还有下一层 (读取下一个 jump)
                # 通过尝试读取并回退判断文件是否结束
                # 注意: NBS 在最后一层结束后直接是 layer count (2B)
                # 这里依赖后续读取层名时的指针位置
                continue
            tick += jump

            # 当前 tick 上的所有音符 (可能多个乐器叠加)
            while True:
                inst_byte = f.read(1)
                if not inst_byte:
                    break
                instrument = inst_byte[0]
                if instrument == 0:
                    break  # 当前 tick 音符序列结束
                key_byte = f.read(1)
                if not key_byte:
                    break
                key = key_byte[0]
                instr_name = NBS_INSTRUMENTS.get(instrument, "harp")
                pitch = _nbs_key_to_pitch(key)
                result.add(Note(instrument=instr_name, pitch=pitch, velocity=100, tick=tick - 1))
    except (struct.error, IndexError):
        # 读取到末尾或解析失败, 退出循环进入层名阶段
        pass

    # 层名与计数 (可选, 后续版本中包含)
    # 旧版没有 layer count 字段, 跳过剩余解析
    try:
        # 新版在音符数据后有 layer_count(2B) + 每层 name + volume
        pos_before = f.tell()
        layer_count = _u16(f)
        # 简单合理性检查: layer_count 与已识别的层数接近
        if abs(layer_count - (layer_index + 1)) <= 2:
            for _ in range(layer_count):
                _read_string(f)
                _u8(f)  # volume
                if version >= 4:
                    _u8(f)  # panning
                    _read_string(f)  # panning name
        else:
            # 不匹配, 回退指针
            f.seek(pos_before)
    except (struct.error, IndexError):
        # 层名解析失败不影响音符数据
        pass

    # tempo: ticks per second (新版在文件末尾)
    try:
        tempo_small = _u16(f)
        if 0 < tempo_small < 1000:
            result.tempo = tempo_small
        else:
            # 可能是 4 字节 float (新版>=3)
            pass
    except struct.error:
        pass

    # 兜底: 新版 tempo 字段可能为 4 字节
    if result.tempo == 10 and version >= 1:
        try:
            f.seek(-6, io.SEEK_END)
            (tempo_4b,) = struct.unpack("<I", f.read(4))
            if 0 < tempo_4b < 100000:
                result.tempo = tempo_4b
        except (struct.error, OSError):
            pass

    return result
