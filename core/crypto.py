# -*- coding: utf-8 -*-
"""加密引擎 / encryption engine.

为 .baia 加密建筑格式提供:
- 密钥派生: PBKDF2-HMAC-SHA256 (100,000 次迭代)
- 流加密: 基于 SHA256 的密钥流 XOR (无外部依赖, PyInstaller 友好)
- 完整性: HMAC-SHA256
- 随机盐: 16 字节 os.urandom

设计目标: 保护创作者建筑作品的商业售卖, 防止未授权解密。
非军事级加密, 但足以阻止普通用户破解。
"""
import os
import hmac
import hashlib
import struct
import secrets

PBKDF2_ITERATIONS = 100_000
KEY_LEN = 32  # 256 位密钥
SALT_LEN = 16
HMAC_LEN = 32


def derive_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """PBKDF2 派生密钥 / derive key from password + salt."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, KEY_LEN)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """基于 SHA256 的密钥流 / SHA256-based keystream.

    用 (key + nonce + counter) 做 SHA256 拉伸为密钥流, 类似 ChaCha20 计数器模式。
    """
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt(plaintext: bytes, password: str) -> tuple:
    """加密 / encrypt plaintext.

    Returns:
        (ciphertext, salt, nonce, hmac_tag)
    """
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(SALT_LEN)
    key = derive_key(password, salt)
    ks = _keystream(key, nonce, len(plaintext))
    ciphertext = bytes(p ^ k for p, k in zip(plaintext, ks))
    tag = hmac.new(key, salt + nonce + ciphertext, hashlib.sha256).digest()
    return ciphertext, salt, nonce, tag


def decrypt(ciphertext: bytes, password: str, salt: bytes, nonce: bytes, tag: bytes) -> bytes:
    """解密 / decrypt ciphertext.

    Raises:
        ValueError: HMAC 校验失败 (密码错误或数据被篡改)
    """
    key = derive_key(password, salt)
    expected_tag = hmac.new(key, salt + nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("授权码错误或文件已损坏 / invalid license key or corrupted file")
    ks = _keystream(key, nonce, len(ciphertext))
    plaintext = bytes(c ^ k for c, k in zip(ciphertext, ks))
    return plaintext


def random_token(nbytes: int = 8) -> str:
    """生成随机令牌 (用于授权码) / generate random token."""
    return secrets.token_hex(nbytes).upper()


def hash_hex(data: bytes) -> str:
    """SHA256 哈希 / SHA256 hash hex."""
    return hashlib.sha256(data).hexdigest()
