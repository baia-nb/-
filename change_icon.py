# -*- coding: utf-8 -*-
"""用溯茸之冬图片替换 EXE 图标 (14字节 GRPICONDIRENTRY 格式)。"""
import os
import sys
import ctypes
import struct
import shutil
from ctypes import wintypes
from PIL import Image
import pefile

ROOT = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(ROOT, "dist", "我的世界格式转换器.exe")
IMG_PATH = os.path.join(ROOT, "微信图片_20260812152112_50_11111114.jpg")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.BeginUpdateResourceW.restype = wintypes.HANDLE
kernel32.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
kernel32.UpdateResourceW.restype = wintypes.BOOL
kernel32.UpdateResourceW.argtypes = [
    wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.WORD, wintypes.LPVOID, wintypes.DWORD,
]
kernel32.EndUpdateResourceW.restype = wintypes.BOOL
kernel32.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]


def _int_id(val):
    return ctypes.cast(ctypes.c_void_p(val), wintypes.LPCWSTR)


def _str_id(s):
    return ctypes.c_wchar_p(s)


def img_to_ico(img_path, ico_path):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    if w != h:
        side = min(w, h)
        img = img.crop(((w-side)//2, (h-side)//2, (w-side)//2+side, (h-side)//2+side))
    sizes = [256, 128, 64, 48, 32, 16]
    images = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    return ico_path


def parse_ico(ico_path):
    with open(ico_path, "rb") as f:
        data = f.read()
    _, _, count = struct.unpack_from("<HHH", data, 0)
    entries = []
    offset = 6
    for _ in range(count):
        bW, bH, bCC, bR, wPlanes, wBC, dwSize, dwOff = \
            struct.unpack_from("<BBBBHHII", data, offset)
        entries.append({
            "w": bW if bW != 0 else 256, "h": bH if bH != 0 else 256,
            "cc": bCC, "planes": wPlanes, "bpp": wBC,
            "data": data[dwOff:dwOff+dwSize], "size": dwSize,
        })
        offset += 16
    return count, entries


def enum_icon_resources(exe_path):
    pe = pefile.PE(exe_path, fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
    groups, icons = [], []
    if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        for e in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if e.id == pefile.RESOURCE_TYPE["RT_GROUP_ICON"]:
                for grp in e.directory.entries:
                    if grp.name is not None:
                        groups.append((grp.name.string.decode("utf-8", "replace"), True))
                    else:
                        groups.append((grp.id, False))
            elif e.id == pefile.RESOURCE_TYPE["RT_ICON"]:
                for ic in e.directory.entries:
                    if ic.name is not None:
                        icons.append((ic.name.string.decode("utf-8", "replace"), True))
                    else:
                        icons.append((ic.id, False))
    pe.close()
    return groups, icons


def get_overlay_start(exe_path):
    pe = pefile.PE(exe_path)
    last = pe.sections[-1]
    start = last.PointerToRawData + last.SizeOfRawData
    pe.close()
    return start


def replace_exe_icon(exe_path, ico_path):
    count, entries = parse_ico(ico_path)
    overlay_start = get_overlay_start(exe_path)
    with open(exe_path, "rb") as f:
        original_data = f.read()
    pe_only = original_data[:overlay_start]
    overlay_data = original_data[overlay_start:]

    tmp_path = exe_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(pe_only)

    old_groups, old_icons = enum_icon_resources(tmp_path)
    hUpdate = kernel32.BeginUpdateResourceW(tmp_path, False)
    if not hUpdate:
        os.remove(tmp_path)
        raise RuntimeError(f"BeginUpdateResourceW 失败: {ctypes.get_last_error()}")

    try:
        RT_ICON, RT_GROUP_ICON, LANG_NEUTRAL = 3, 14, 0
        for name, is_str in old_groups:
            name_ptr = _str_id(name) if is_str else _int_id(name)
            kernel32.UpdateResourceW(hUpdate, _int_id(RT_GROUP_ICON),
                                     name_ptr, LANG_NEUTRAL, None, 0)
        for name, is_str in old_icons:
            name_ptr = _str_id(name) if is_str else _int_id(name)
            kernel32.UpdateResourceW(hUpdate, _int_id(RT_ICON),
                                     name_ptr, LANG_NEUTRAL, None, 0)

        base_id = 1
        for idx, ent in enumerate(entries):
            buf = ctypes.create_string_buffer(ent["data"])
            kernel32.UpdateResourceW(hUpdate, _int_id(RT_ICON),
                                    _int_id(base_id + idx), LANG_NEUTRAL,
                                    buf, len(ent["data"]))

        grp = bytearray(struct.pack("<HHH", 0, 1, count))
        for idx, ent in enumerate(entries):
            w_f = ent["w"] if ent["w"] != 256 else 0
            h_f = ent["h"] if ent["h"] != 256 else 0
            grp.extend(struct.pack("<BBBBHHIH",
                w_f, h_f, ent["cc"], 0,
                ent["planes"], ent["bpp"], ent["size"], base_id + idx))
        buf = ctypes.create_string_buffer(bytes(grp))
        kernel32.UpdateResourceW(hUpdate, _int_id(RT_GROUP_ICON),
                                 _int_id(1), LANG_NEUTRAL, buf, len(grp))
        kernel32.UpdateResourceW(hUpdate, _int_id(RT_GROUP_ICON),
                                 _str_id("MAINICON"), LANG_NEUTRAL,
                                 buf, len(grp))
        kernel32.EndUpdateResourceW(hUpdate, False)
    except Exception:
        kernel32.EndUpdateResourceW(hUpdate, True)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    with open(tmp_path, "rb") as f:
        modified_pe = f.read()
    with open(tmp_path, "wb") as f:
        f.write(modified_pe)
        f.write(overlay_data)
    os.replace(tmp_path, exe_path)
    return True


def main():
    if not os.path.exists(EXE_PATH):
        print(f"[错误] EXE 不存在: {EXE_PATH}"); sys.exit(1)
    if not os.path.exists(IMG_PATH):
        print(f"[错误] 图片不存在: {IMG_PATH}"); sys.exit(1)

    backup_path = EXE_PATH + ".bak"
    shutil.copy2(EXE_PATH, backup_path)
    print(f"[备份] {backup_path}")

    print("[图标] 生成 ICO...")
    ico_path = os.path.join(ROOT, "mc_icon.ico")
    img_to_ico(IMG_PATH, ico_path)

    print("[图标] 替换 EXE 图标...")
    try:
        replace_exe_icon(EXE_PATH, ico_path)
    except Exception as e:
        print(f"[错误] {e}")
        shutil.copy2(backup_path, EXE_PATH)
        sys.exit(1)

    print(f"[完成] EXE: {os.path.getsize(EXE_PATH)} bytes")
    try:
        os.remove(ico_path); os.remove(backup_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()