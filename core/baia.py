# -*- coding: utf-8 -*-
""".baia 加密建筑格式 / .baia encrypted building format.

格式结构 (参考 .ibi 但加入授权码验证):
+----------+----------------------+
| 偏移     | 字段                  |
+----------+----------------------+
| 0        | 魔数 "BAIA" (4B)      |
| 4        | 版本 (1B)             |
| 5        | 元数据长度 (2B, BE)   |
| 7        | 元数据 JSON (N B)      |
| 7+N      | 文件 ID (8B ASCII)    |
| 15+N     | 盐 (16B)              |
| 31+N     | nonce (16B)           |
| 47+N     | 密文长度 (4B, BE)      |
| 51+N     | 密文 (M B)            |
| 51+N+M   | HMAC-SHA256 (32B)     |
+----------+----------------------+

元数据 JSON:
{
    "name": "建筑名称",
    "author": "创作者",
    "source_format": "mcstructure",  # 原始格式
    "source_size": 12345,            # 原始大小
    "created": "2026-08-13",         # 加密日期
    "tier": "trial",                 # 默认授权等级
    "price": 0,                       # 建议价格
    "description": "建筑描述"
}

加密密钥 = 授权码 (license key)
- 试用授权码: 解密后应用试用限制
- 付费授权码: 解密后无限制
"""
import os
import json
import struct
from datetime import date
from .crypto import encrypt, decrypt
from .license import (
    compute_file_id,
    generate_license,
    verify_license,
    extract_tier,
    apply_trial_limits,
)
from .paths import default_output_path, ensure_dir, get_desktop_dir

BAIA_MAGIC = b"BAIA"
BAIA_VERSION = 1


def write_baia(plaintext: bytes, creator_secret: str, metadata: dict,
               out_path: str = None, name: str = None) -> tuple:
    """加密建筑数据为 .baia 文件 / encrypt to .baia.

    流程: 计算 file_id → 用 creator_secret 生成授权码 → 授权码作为加密密码。

    Args:
        plaintext: 原始建筑数据 (setblock 指令文本)
        creator_secret: 创作者主密钥 (用于生成授权码, 同时是解密根密钥)
        metadata: 元数据 (name/author/source_format/price/tier 等)
        out_path: 输出路径
        name: 文件名

    Returns:
        (output_path, file_id, license_key)
        license_key = BAIA-XXXX-XXXX-XXXX-XXXX, 卖给买家用于解密
    """
    file_id = compute_file_id(plaintext)
    tier = metadata.get("tier", "trial")

    # 用 creator_secret 生成授权码 (BAIA-XXXX), 同时作为加密密码
    license_key = generate_license(creator_secret, file_id, tier)

    # 元数据
    meta = {
        "name": metadata.get("name", name or "untitled"),
        "author": metadata.get("author", "unknown"),
        "source_format": metadata.get("source_format", "txt"),
        "source_size": len(plaintext),
        "created": date.today().isoformat(),
        "tier": tier,
        "price": metadata.get("price", 0),
        "description": metadata.get("description", ""),
        "file_id": file_id,
    }
    meta_json = json.dumps(meta, ensure_ascii=False).encode("utf-8")

    # 用授权码作为密码加密
    ciphertext, salt, nonce, tag = encrypt(plaintext, license_key)

    # 输出路径
    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        fname = (name or meta["name"]) + ".baia"
        out_path = os.path.join(out_dir, fname)

    # 组装
    with open(out_path, "wb") as f:
        f.write(BAIA_MAGIC)
        f.write(bytes([BAIA_VERSION]))
        f.write(struct.pack(">H", len(meta_json)))
        f.write(meta_json)
        f.write(file_id.encode("ascii"))
        f.write(salt)
        f.write(nonce)
        f.write(struct.pack(">I", len(ciphertext)))
        f.write(ciphertext)
        f.write(tag)

    return out_path, file_id, license_key


def read_baia(path: str, license_key: str, apply_limits: bool = True) -> dict:
    """解密 .baia 文件 / decrypt .baia.

    Args:
        path: .baia 文件路径
        license_key: 授权码
        apply_limits: 是否应用试用限制

    Returns:
        {
            "valid": bool,
            "error": str (失败时),
            "plaintext": bytes (成功时),
            "metadata": dict,
            "tier": str,
            "out_path": str (如已写出到文件)
        }
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        return {"valid": False, "error": f"文件读取失败: {e}"}

    if len(data) < 7 or data[:4] != BAIA_MAGIC:
        return {"valid": False, "error": "不是有效的 .baia 文件"}

    version = data[4]
    if version != BAIA_VERSION:
        return {"valid": False, "error": f"不支持的 .baia 版本: {version}"}

    try:
        meta_len = struct.unpack(">H", data[5:7])[0]
        meta_json = data[7:7+meta_len]
        metadata = json.loads(meta_json.decode("utf-8"))
        offset = 7 + meta_len
        file_id = data[offset:offset+8].decode("ascii")
        offset += 8
        salt = data[offset:offset+16]
        offset += 16
        nonce = data[offset:offset+16]
        offset += 16
        cipher_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        ciphertext = data[offset:offset+cipher_len]
        offset += cipher_len
        tag = data[offset:offset+32]
    except (IndexError, struct.error, json.JSONDecodeError) as e:
        return {"valid": False, "error": f"文件结构损坏: {e}"}

    # 解密 (授权码 = 解密密码; HMAC 失败说明授权码错误)
    try:
        plaintext = decrypt(ciphertext, license_key, salt, nonce, tag)
    except ValueError as e:
        return {"valid": False, "error": str(e), "metadata": metadata}

    # 验证 file_id
    actual_file_id = compute_file_id(plaintext)
    if actual_file_id != file_id:
        return {"valid": False, "error": "文件 ID 不匹配 (数据可能被篡改)"}

    # 从授权码提取授权等级 (无需 creator_secret, HMAC 已证明授权码有效)
    tier = extract_tier(license_key)

    # 应用试用限制
    if apply_limits:
        plaintext = apply_trial_limits(plaintext, tier)

    return {
        "valid": True,
        "plaintext": plaintext,
        "metadata": metadata,
        "tier": tier,
        "file_id": file_id,
    }


def read_baia_metadata(path: str) -> dict:
    """仅读取 .baia 元数据 (无需授权码) / read metadata only.

    买家可以预览建筑信息后再决定是否购买授权码。
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        return {"valid": False, "error": f"文件读取失败: {e}"}

    if len(data) < 7 or data[:4] != BAIA_MAGIC:
        return {"valid": False, "error": "不是有效的 .baia 文件"}

    try:
        meta_len = struct.unpack(">H", data[5:7])[0]
        meta_json = data[7:7+meta_len]
        metadata = json.loads(meta_json.decode("utf-8"))
        return {"valid": True, "metadata": metadata}
    except Exception as e:
        return {"valid": False, "error": f"元数据解析失败: {e}"}
