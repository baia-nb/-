# -*- coding: utf-8 -*-
"""Schematic 格式读取器 / legacy MCEdit .schematic reader.

NBT (gzip, 大端)。字段: Width/Height/Length (short), Blocks (byte[]),
Data (byte[]), 可选 AddBlocks (byte[], 高/低 4 位补 ID>255), Materials (string)。
方块按 YZX 顺序存储: index = (y*Length + z)*Width + x。
方块 ID 为有符号字节, 需转无符号; 用简化 ID->name 映射。
参考 Exchange Tool v13.0。
"""
from ..model import Structure, Block
from ..nbt import parse, to_plain, Tag

# 简化的经典方块 ID 映射 (Beta / 1.12 时代)
LEGACY_ID_MAP = {
    0: "minecraft:air", 1: "minecraft:stone", 2: "minecraft:grass_block", 3: "minecraft:dirt",
    4: "minecraft:cobblestone", 5: "minecraft:oak_planks", 7: "minecraft:bedrock",
    8: "minecraft:water", 9: "minecraft:water", 10: "minecraft:lava", 11: "minecraft:lava",
    12: "minecraft:sand", 13: "minecraft:gravel", 14: "minecraft:gold_ore", 15: "minecraft:iron_ore",
    16: "minecraft:coal_ore", 17: "minecraft:oak_log", 18: "minecraft:oak_leaves",
    19: "minecraft:sponge", 20: "minecraft:glass", 21: "minecraft:lapis_ore", 22: "minecraft:lapis_block",
    23: "minecraft:dispenser", 24: "minecraft:sandstone", 25: "minecraft:note_block",
    35: "minecraft:white_wool", 41: "minecraft:gold_block", 42: "minecraft:iron_block",
    43: "minecraft:stone_bricks", 44: "minecraft:stone_brick_slab", 45: "minecraft:bricks",
    46: "minecraft:tnt", 47: "minecraft:bookshelf", 48: "minecraft:mossy_cobblestone",
    49: "minecraft:obsidian", 50: "minecraft:torch", 53: "minecraft:oak_stairs",
    54: "minecraft:chest", 57: "minecraft:diamond_block", 58: "minecraft:crafting_table",
    61: "minecraft:furnace", 62: "minecraft:furnace", 64: "minecraft:oak_door",
    65: "minecraft:ladder", 66: "minecraft:rail", 67: "minecraft:cobblestone_stairs",
    73: "minecraft:redstone_ore", 74: "minecraft:redstone_ore", 76: "minecraft:redstone_torch",
    77: "minecraft:stone_button", 78: "minecraft:snow", 79: "minecraft:ice",
    80: "minecraft:snow_block", 81: "minecraft:cactus", 82: "minecraft:clay",
    84: "minecraft:jukebox", 85: "minecraft:oak_fence", 87: "minecraft:netherrack",
    88: "minecraft:soul_sand", 89: "minecraft:glowstone", 91: "minecraft:jack_o_lantern",
    95: "minecraft:white_stained_glass", 98: "minecraft:stone_bricks",
    99: "minecraft:brown_mushroom_block", 100: "minecraft:red_mushroom_block",
    101: "minecraft:iron_bars", 102: "minecraft:glass_pane", 103: "minecraft:melon",
    112: "minecraft:nether_bricks", 113: "minecraft:nether_brick_fence",
    114: "minecraft:nether_brick_stairs", 116: "minecraft:enchanting_table",
    121: "minecraft:end_stone", 123: "minecraft:redstone_lamp", 125: "minecraft:oak_slab",
    126: "minecraft:oak_slab", 128: "minecraft:sandstone_stairs", 130: "minecraft:ender_chest",
    133: "minecraft:emerald_block", 138: "minecraft:beacon", 139: "minecraft:cobblestone_wall",
    145: "minecraft:anvil", 152: "minecraft:redstone_block", 153: "minecraft:quartz_ore",
    155: "minecraft:quartz_block", 156: "minecraft:quartz_stairs", 157: "minecraft:activator_rail",
    158: "minecraft:dropper", 159: "minecraft:white_terracotta", 165: "minecraft:slime_block",
    170: "minecraft:hay_block", 173: "minecraft:coal_block", 174: "minecraft:packed_ice",
    179: "minecraft:red_sandstone", 246: "minecraft:structure_block",
}


def _id_to_name(block_id: int) -> str:
    return LEGACY_ID_MAP.get(block_id, f"minecraft:block_{block_id}")


def read_schematic(path) -> Structure:
    """读取旧版 .schematic 建筑文件 / read legacy schematic file."""
    with open(path, "rb") as f:
        data = f.read()
    plain = to_plain(parse(data, little_endian=False, compressed=True))
    st = Structure(format="schematic")
    if not isinstance(plain, dict):
        return st

    width = int(plain.get("Width", 0))
    height = int(plain.get("Height", 0))
    length = int(plain.get("Length", 0))
    st.size = (width, height, length)

    blocks = plain.get("Blocks") or []
    block_data = plain.get("Data") or []
    add = plain.get("AddBlocks") or []

    st.origin = (
        int(plain.get("WEOffsetX", 0)),
        int(plain.get("WEOffsetY", 0)),
        int(plain.get("WEOffsetZ", 0)),
    )

    def get_id(j: int) -> int:
        bid = blocks[j] & 0xFF if j < len(blocks) else 0
        ai = j >> 1
        if add and ai < len(add):
            ab = add[ai] & 0xFF
            # 偶数索引取高 4 位, 奇数索引取低 4 位 (WorldEdit/MCEdit 约定)
            extra = (ab >> 4) & 0x0F if (j & 1) == 0 else ab & 0x0F
            bid |= extra << 8
        return bid

    # index = (y * Length + z) * Width + x  (YZX 顺序)
    for y in range(height):
        for z in range(length):
            base = (y * length + z) * width
            for x in range(width):
                idx = base + x
                bid = get_id(idx)
                if bid == 0:
                    continue
                dval = block_data[idx] & 0x0F if idx < len(block_data) else 0
                st.add(Block(name=_id_to_name(bid), data=dval,
                             nbt_data={"pos": (x, y, z), "legacy_id": bid}))
    return st
