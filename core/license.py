# -*- coding: utf-8 -*-
"""授权码系统 / license system.

为 .baia 加密建筑格式提供:
- 授权码生成: BAIA-XXXX-XXXX-XXXX-XXXX 格式
- 授权码验证: 基于创作者密钥 + 文件盐
- 试用/付费分级: 试用版限制方块数/带水印, 付费版无限制
- 机器码绑定(可选): 授权码绑定到买家机器

设计:
- 创作者密钥 (creator_secret): 创作者在程序中设置的密码, 用于生成和验证授权码
- 文件 ID (file_id): 每个加密文件唯一 ID, 嵌入授权码
- 授权码 = base32(creator_secret_hash + file_id + tier + checksum)
"""
import os
import hmac
import hashlib
import base64
import struct
import uuid
from .crypto import derive_key, random_token


def get_machine_id() -> str:
    """获取机器码 (用于绑定授权) / get machine fingerprint."""
    try:
        # Windows: 用卷序列号 + 计算机名
        import subprocess
        result = subprocess.run(["vol", "C:"], capture_output=True, text=True, shell=True)
        vol_info = result.stdout + result.stderr
        return hashlib.sha256(vol_info.encode("utf-8")).hexdigest()[:32]
    except Exception:
        # 回退: 用 uuid
        return hashlib.sha256(uuid.getnode().to_bytes(6, "big")).hexdigest()[:32]


def generate_creator_secret() -> str:
    """生成创作者主密钥 / generate creator master secret.

    创作者应妥善保存, 用于生成所有授权码。
    """
    return random_token(16)  # 32 字符


def compute_file_id(plaintext: bytes) -> str:
    """计算文件唯一 ID (8 字符) / compute file unique ID."""
    return hashlib.sha256(plaintext).hexdigest()[:8].upper()


def generate_license(creator_secret: str, file_id: str, tier: str,
                     machine_id: str = None) -> str:
    """生成授权码 / generate license key.

    Args:
        creator_secret: 创作者主密钥
        file_id: 文件 ID (8 字符)
        tier: "trial" / "paid" / "full"
        machine_id: 可选机器码绑定

    Returns:
        授权码字符串 "BAIA-XXXX-XXXX-XXXX-XXXX"
    """
    tier_map = {"trial": 1, "paid": 2, "full": 3}
    tier_num = tier_map.get(tier, 1)

    # 载荷: file_id(8) + tier(1) + machine_binding(0 or 16)
    payload = file_id.encode("ascii") + bytes([tier_num])
    if machine_id:
        payload += machine_id.encode("ascii")[:16]

    # 签名: creator_secret + payload, 取前 6 字节 (与验证一致)
    sig = hashlib.sha256(creator_secret.encode("utf-8") + payload).digest()[:6]

    # 组合: payload(9 字节) + sig(6 字节) = 15 字节 → base32 = 24 字符
    raw = payload + sig
    # base32 编码 → 去填充
    b32 = base64.b32encode(raw).decode("ascii").rstrip("=")
    # 必须用 8 字符的倍数 (每个 8 字符 = 5 字节), 取 24 字符 = 15 字节
    # payload(file_id 8 + tier 1) + sig(8) = 17 字节 -> base32 = 28 字符
    # 取前 24 字符 = 15 字节 (前 8 字节 payload + 7 字节 sig), 足够验证
    b32 = b32[:24]
    parts = [b32[i:i+6] for i in range(0, 24, 6)]
    return "BAIA-" + "-".join(parts)


def extract_tier(license_key: str) -> str:
    """从授权码提取授权等级 (无需创作者密钥) / extract tier without secret.

    仅解码授权码内嵌的 tier, 不验证签名。
    签名验证由 HMAC (解密时) 隐式完成: 错误的授权码无法解密。
    """
    if not license_key.startswith("BAIA-"):
        return "trial"
    parts = license_key[5:].split("-")
    if len(parts) != 4 or not all(len(p) == 6 for p in parts):
        return "trial"
    b32 = "".join(parts)
    try:
        raw = base64.b32decode(b32)
    except Exception:
        return "trial"
    if len(raw) < 9:
        return "trial"
    tier_num = raw[8]
    tier_map = {1: "trial", 2: "paid", 3: "full"}
    return tier_map.get(tier_num, "trial")


def verify_license(license_key: str, creator_secret: str, file_id: str) -> dict:
    """验证授权码 / verify license key.

    Returns:
        {"valid": bool, "tier": str, "machine_bound": bool}
    """
    if not license_key.startswith("BAIA-"):
        return {"valid": False, "error": "授权码格式错误"}

    parts = license_key[5:].split("-")
    if len(parts) != 4 or not all(len(p) == 6 for p in parts):
        return {"valid": False, "error": "授权码格式错误"}

    b32 = "".join(parts)  # 4 × 6 = 24 字符
    # base32 标准解码 (24 字符 = 3 块 × 8 字符 = 15 字节)
    try:
        raw = base64.b32decode(b32)
    except Exception:
        return {"valid": False, "error": "授权码解码失败"}

    if len(raw) < 9:
        return {"valid": False, "error": "授权码长度不足"}

    # 解析: payload(9 字节 = file_id 8 + tier 1) + sig(6 字节, 截断自 8)
    sig = raw[9:15]  # 取 6 字节 sig (从原始 8 字节截断)
    payload = raw[:9]
    fid = payload[:8].decode("ascii", errors="replace")
    tier_num = payload[8] if len(payload) > 8 else 0
    machine_bound = len(payload) > 9

    # 验证签名 (用前 6 字节, 与生成时一致)
    expected_sig = hashlib.sha256(creator_secret.encode("utf-8") + payload).digest()[:6]
    if not hmac.compare_digest(sig, expected_sig):
        return {"valid": False, "error": "授权码签名无效"}

    # 验证 file_id
    if fid != file_id:
        return {"valid": False, "error": f"授权码不属于此文件 (期望 {file_id}, 实际 {fid})"}

    # 机器码绑定验证
    if machine_bound:
        bound_mid = payload[9:25].decode("ascii", errors="replace")
        current_mid = get_machine_id()[:16]
        if bound_mid != current_mid:
            return {"valid": False, "error": "授权码已绑定其他设备"}

    tier_map = {1: "trial", 2: "paid", 3: "full"}
    tier = tier_map.get(tier_num, "trial")
    return {"valid": True, "tier": tier, "machine_bound": machine_bound}


# 试用限制配置
TRIAL_LIMITS = {
    "trial": {
        "max_blocks": 500,      # 试用版最多 500 个方块
        "watermark": True,      # 带水印
        "expires_days": 7,      # 7 天后过期
    },
    "paid": {
        "max_blocks": -1,       # 无限制
        "watermark": False,
        "expires_days": -1,     # 永久
    },
    "full": {
        "max_blocks": -1,
        "watermark": False,
        "expires_days": -1,
        "commercial": True,     # 允许商业用途
    },
}


def get_tier_limits(tier: str) -> dict:
    """获取授权等级限制 / get tier limits."""
    return TRIAL_LIMITS.get(tier, TRIAL_LIMITS["trial"])


def apply_trial_limits(plaintext: bytes, tier: str) -> bytes:
    """对试用版应用限制(加水印/截断) / apply trial limits.

    - 试用版: 在文本头部插入水印注释, 超过 max_blocks 的部分截断
    - 付费版: 原样返回
    """
    if tier == "trial":
        limits = get_tier_limits("trial")
        text = plaintext.decode("utf-8", errors="replace")
        lines = text.splitlines()

        # 截断超过限制的方块
        if limits["max_blocks"] > 0:
            kept = []
            block_count = 0
            for line in lines:
                if line.strip().startswith("setblock"):
                    block_count += 1
                    if block_count > limits["max_blocks"]:
                        break
                kept.append(line)
            text = "\n".join(kept)

        # 加水印
        if limits["watermark"]:
            watermark = (
                "# ============================================================\n"
                "#  试用版 - 未授权完整内容\n"
                f"#  限制: 最多 {limits['max_blocks']} 个方块, 试用 {limits['expires_days']} 天\n"
                "#  购买完整授权码后可解锁全部内容\n"
                "# ============================================================\n"
            )
            text = watermark + text

        return text.encode("utf-8")

    return plaintext
