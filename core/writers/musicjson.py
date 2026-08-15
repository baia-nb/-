# -*- coding: utf-8 -*-
"""音乐播放 JSON 写入器 / music play JSON writer.

输出 JSON:
    {
      "name": ...,
      "tempo": ...,
      "ppq": ...,
      "notes": [{"instrument", "pitch", "tick"}, ...],
      "commands": [playsound 指令列表]
    }
"""
import os
import json
from ..paths import get_desktop_dir, ensure_dir


def _playsound_command(note):
    """生成 playsound 指令 / build a playsound command for a note."""
    # pitch: 音符块音高 (0..24) 映射到 playsound 的 0..2 浮点
    pitch = int(note.pitch)
    freq = 2.0 ** ((pitch - 12) / 12.0)
    volume = max(0.0, min(1.0, note.velocity / 100.0))
    sound = f"note.{note.instrument}"
    return f"playsound {sound} @a ~ ~ ~ {volume:.2f} {freq:.4f}"


def write(midi_data, out_path=None, name=None):
    """写入音乐播放 JSON / write music play JSON.

    Args:
        midi_data: MidiData 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    fname = (name or "music") + "_音乐.json"
    tempo = int(getattr(midi_data, "tempo", 500000))
    ppq = int(getattr(midi_data, "ppq", 480))

    notes_out = []
    commands = []
    for note in midi_data.notes:
        notes_out.append({
            "instrument": note.instrument,
            "pitch": int(note.pitch),
            "tick": int(note.tick),
        })
        commands.append(_playsound_command(note))

    data = {
        "name": name or "music",
        "tempo": tempo,
        "ppq": ppq,
        "notes": notes_out,
        "commands": commands,
    }

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        out_path = os.path.join(out_dir, fname)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path
