# -*- coding: utf-8 -*-
"""加密服务插件 / encryption service plugins.

为创作者提供:
1. 建筑加密为 .baia (创作者售卖前加密, 生成买家授权码)
2. 重新生成授权码 (补发丢失的授权码)
3. 解密 .baia 为建筑 (买家输入授权码)
4. 预览 .baia 元数据 (买家购买前查看)

授权模型 (无服务器, 纯离线):
- 创作者主密钥 (creator_secret): 创作者保存, 用于生成授权码
- 授权码 (license_key, BAIA-XXXX 格式): 卖给买家, 同时是解密密码
- 授权等级 (tier): trial(试用,限500方块+水印) / paid(付费,无限制) / full(完整,商业授权)
- 加密时选定等级, 生成对应授权码; 不同等级需分别加密
"""
import os
from plugins.registry import register
from core.paths import default_output_path, get_desktop_dir, ensure_dir, get_subdir
from core.readers import read_structure
from core.writers import write_txt


@register("建筑加密为.baia", "加密服务",
          "把建筑文件加密为 .baia 格式, 生成买家授权码, 用于商业售卖")
def encrypt_building(args):
    """加密建筑文件为 .baia / encrypt building to .baia.

    参数: [输入文件] [创作者主密钥] [授权等级:trial/paid/full(可选,默认trial)] [作者名(可选)] [建筑名(可选)]
    """
    inp = args[0]
    creator_secret = args[1] if len(args) > 1 else None
    tier = args[2] if len(args) > 2 else "trial"
    author = args[3] if len(args) > 3 else "unknown"
    name = args[4] if len(args) > 4 else None

    if tier not in ("trial", "paid", "full"):
        return f"错误: 未知授权等级 {tier}, 支持: trial/paid/full"

    if not creator_secret:
        from core.license import generate_creator_secret
        creator_secret = generate_creator_secret()
        auto_generated = True
    else:
        auto_generated = False

    # 读取建筑文件并转换为 setblock 文本
    from core.readers import detect_format
    fmt = detect_format(inp)
    if not fmt:
        if inp.lower().endswith(".txt"):
            with open(inp, "rb") as f:
                plaintext = f.read()
            source_fmt = "txt"
        else:
            return f"错误: 不支持的输入格式: {inp}"
    else:
        struct = read_structure(inp, fmt)
        from core.writers.txt import write
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False).name
        write(struct, tmp)
        with open(tmp, "rb") as f:
            plaintext = f.read()
        os.remove(tmp)
        source_fmt = fmt

    base = name or os.path.splitext(os.path.basename(inp))[0]
    metadata = {
        "name": base,
        "author": author,
        "source_format": source_fmt,
        "tier": tier,
        "price": 0,
        "description": f"由 {author} 加密的建筑作品",
    }

    from core.baia import write_baia
    out_dir = get_subdir("baia加密")
    out_path = os.path.join(out_dir, f"{base}_{tier}.baia")
    out_path, file_id, license_key = write_baia(
        plaintext, creator_secret, metadata, out_path, base
    )

    tier_desc = {
        "trial": "试用版 (最多500方块, 带水印)",
        "paid": "付费版 (无限制, 永久)",
        "full": "完整版 (无限制, 商业授权)",
    }[tier]

    msg = (
        f"加密成功!\n"
        f"输出文件: {out_path}\n"
        f"文件ID: {file_id}\n"
        f"授权等级: {tier} - {tier_desc}\n"
        f"\n"
        f"===== 买家授权码 (卖给买家) =====\n"
        f"{license_key}\n"
        f"================================\n"
    )
    if auto_generated:
        msg += (
            f"\n创作者主密钥 (已自动生成, 请立即保存!):\n{creator_secret}\n"
            f"⚠️ 丢失后无法补发授权码, 之前加密的文件将无法重新生成授权码。\n"
        )
    else:
        msg += f"\n创作者主密钥: {creator_secret}\n"
    msg += (
        f"\n售卖流程:\n"
        f"1. 将 .baia 文件 + 授权码 发给买家\n"
        f"2. 买家在本程序 '解密.baia为建筑' 中输入两者即可解密\n"
        f"3. 如需其他授权等级, 重新加密一次 (不同等级授权码不同)\n"
        f"4. 授权码丢失? 用 '重新生成授权码' 补发 (需创作者主密钥 + 文件ID)"
    )
    return msg


@register("重新生成授权码", "加密服务",
          "为已加密的 .baia 补发授权码 (需创作者主密钥 + 文件ID)")
def regenerate_license(args):
    """重新生成授权码 / regenerate license key.

    参数: [创作者主密钥] [文件ID] [授权等级:trial/paid/full(可选,默认trial)]
    """
    if len(args) < 2:
        return "用法: 重新生成授权码 <创作者主密钥> <文件ID> [授权等级:trial/paid/full]"

    creator_secret = args[0]
    file_id = args[1]
    tier = args[2] if len(args) > 2 else "trial"

    if tier not in ("trial", "paid", "full"):
        return f"错误: 未知授权等级 {tier}, 支持: trial/paid/full"

    from core.license import generate_license
    lic = generate_license(creator_secret, file_id, tier)
    limits = {
        "trial": "试用版 (最多500方块, 带水印)",
        "paid": "付费版 (无限制, 永久)",
        "full": "完整版 (无限制, 商业授权)",
    }
    return f"授权码: {lic}\n等级: {tier} - {limits[tier]}"


@register("解密.baia为建筑", "加密服务",
          "输入授权码解密 .baia 为 setblock 指令 (买家使用)")
def decrypt_baia(args):
    """解密 .baia 为建筑 / decrypt .baia to building.

    参数: [.baia文件] [授权码]
    """
    if len(args) < 2:
        return "用法: 解密.baia为建筑 <.baia文件> <授权码>"

    inp = args[0]
    license_key = args[1]

    from core.baia import read_baia
    result = read_baia(inp, license_key, apply_limits=True)
    if not result["valid"]:
        return f"解密失败: {result.get('error', '未知错误')}"

    plaintext = result["plaintext"]
    metadata = result["metadata"]
    tier = result["tier"]

    base = metadata.get("name", "decrypted")
    out_dir = ensure_dir(get_desktop_dir())
    out_path = os.path.join(out_dir, f"{base}_decrypted.txt")

    with open(out_path, "wb") as f:
        f.write(plaintext)

    tier_label = {"trial": "试用版", "paid": "付费版", "full": "完整版"}.get(tier, tier)
    return (
        f"解密成功!\n"
        f"输出: {out_path}\n"
        f"授权等级: {tier_label}\n"
        f"原始建筑: {metadata.get('name', '未知')} by {metadata.get('author', '未知')}"
    )


@register("预览.baia元数据", "加密服务",
          "查看 .baia 文件信息 (无需授权码, 买家购买前预览)")
def preview_baia(args):
    """预览 .baia 元数据 / preview .baia metadata.

    参数: [.baia文件]
    """
    if len(args) < 1:
        return "用法: 预览.baia元数据 <.baia文件>"

    inp = args[0]
    from core.baia import read_baia_metadata
    result = read_baia_metadata(inp)
    if not result["valid"]:
        return f"读取失败: {result.get('error', '未知错误')}"

    meta = result["metadata"]
    tier_label = {"trial": "试用版", "paid": "付费版", "full": "完整版"}.get(
        meta.get("tier", ""), meta.get("tier", "未知")
    )
    lines = [
        f"建筑名称: {meta.get('name', '未知')}",
        f"作者: {meta.get('author', '未知')}",
        f"原始格式: {meta.get('source_format', '未知')}",
        f"原始大小: {meta.get('source_size', 0)} bytes",
        f"加密日期: {meta.get('created', '未知')}",
        f"文件ID: {meta.get('file_id', '未知')}",
        f"授权等级: {tier_label}",
        f"建议价格: {meta.get('price', 0)} 元",
        f"描述: {meta.get('description', '无')}",
    ]
    return "\n".join(lines)


@register("生成创作者密钥", "加密服务",
          "生成创作者主密钥 (首次使用加密服务前生成, 妥善保存)")
def gen_creator_secret(args):
    """生成创作者主密钥 / generate creator master secret."""
    from core.license import generate_creator_secret
    secret = generate_creator_secret()
    return (
        f"创作者主密钥: {secret}\n\n"
        f"请妥善保存! 丢失后无法补发, 之前加密的文件将无法重新生成授权码。"
    )


@register("查看机器码", "加密服务",
          "查看本机机器码 (用于机器绑定授权码)")
def show_machine_id(args):
    """查看机器码 / show machine ID."""
    from core.license import get_machine_id
    mid = get_machine_id()
    return (
        f"本机机器码: {mid}\n\n"
        f"将此机器码提供给卖家, 卖家可生成绑定到此设备的授权码。"
    )
