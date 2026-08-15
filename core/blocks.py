# -*- coding: utf-8 -*-
"""方块映射表 / block mapping tables.

参考 Exchange Tool v13.0 的功能需求, 提供:
  - 重力方块集合 GRAVITY_BLOCKS
  - 命令方块集合 COMMAND_BLOCKS
  - Java -> Bedrock 方块名映射 JAVA_TO_BEDROCK
  - 像素画方块颜色映射 PIXELART_BLOCKS  ( (r, g, b) -> "minecraft:xxx" )
  - Bedrock 数字 ID -> 名称映射 BEDROCK_BLOCK_IDS
  - 颜色匹配辅助函数 find_closest_block / get_block_id

不依赖任何外部库, 纯常量集合, 供各格式读写器复用.
"""

# ---------------------------------------------------------------------------
# 1. 受重力影响的方块 / gravity-affected blocks
#    这些方块下方无支撑时会掉落, 导入结构时需要在下方放置 barrier 支撑
# ---------------------------------------------------------------------------
GRAVITY_BLOCKS = {
    # 沙类
    "sand", "red_sand", "gravel",
    # 混凝土粉末 (16 色)
    "concrete_powder",
    "white_concrete_powder", "orange_concrete_powder", "magenta_concrete_powder",
    "light_blue_concrete_powder", "yellow_concrete_powder", "lime_concrete_powder",
    "pink_concrete_powder", "gray_concrete_powder", "light_gray_concrete_powder",
    "cyan_concrete_powder", "purple_concrete_powder", "blue_concrete_powder",
    "brown_concrete_powder", "green_concrete_powder", "red_concrete_powder",
    "black_concrete_powder",
    # 其它重力方块
    "anvil", "chipped_anvil", "damaged_anvil",
    "dragon_egg",
    "scaffolding",
    "pointed_dripstone",
    "suspicious_sand",
    "suspicious_gravel",
    # 通用可掉落标识 (某些自定义/快照版本)
    "fallable_block",
}


# ---------------------------------------------------------------------------
# 2. 命令方块集合 / command blocks
# ---------------------------------------------------------------------------
COMMAND_BLOCKS = {
    "command_block",          # 脉冲命令方块
    "chain_command_block",    # 连锁命令方块
    "repeating_command_block",  # 循环命令方块
}


# ---------------------------------------------------------------------------
# 3. Java -> Bedrock 方块名映射 / Java to Bedrock block name mapping
#    现代 Java/Bedrock 方块名基本一致, 这里列出需要转换或常被读写的常见方块.
#    key = Java 名称 (不含 minecraft: 前缀), value = Bedrock 名称
#    (Bedrock 常以 data 值区分变体, 因此颜色变体多映射到同一基础名)
# ---------------------------------------------------------------------------
JAVA_TO_BEDROCK = {
    # 基础方块
    "stone": "stone",
    "granite": "stone",
    "diorite": "stone",
    "andesite": "stone",
    "dirt": "dirt",
    "grass_block": "grass",
    "coarse_dirt": "dirt",
    "podzol": "dirt",
    "mycelium": "mycelium",
    "cobblestone": "cobblestone",
    "mossy_cobblestone": "mossy_cobblestone",
    "bedrock": "bedrock",
    "sand": "sand",
    "red_sand": "sand",
    "gravel": "gravel",
    "clay": "clay",
    "snow_block": "snow",
    "snow": "snow_layer",
    "ice": "ice",
    "packed_ice": "packed_ice",
    "blue_ice": "blue_ice",
    "frosted_ice": "ice",
    # 原木 / 木板
    "oak_log": "log",
    "spruce_log": "log",
    "birch_log": "log",
    "jungle_log": "log",
    "acacia_log": "log2",
    "dark_oak_log": "log2",
    "oak_planks": "planks",
    "spruce_planks": "planks",
    "birch_planks": "planks",
    "jungle_planks": "planks",
    "acacia_planks": "planks",
    "dark_oak_planks": "planks",
    "oak_leaves": "leaves",
    "spruce_leaves": "leaves",
    "birch_leaves": "leaves",
    "jungle_leaves": "leaves",
    "acacia_leaves": "leaves2",
    "dark_oak_leaves": "leaves2",
    # 矿石与矿物块
    "gold_ore": "gold_ore",
    "iron_ore": "iron_ore",
    "coal_ore": "coal_ore",
    "diamond_ore": "diamond_ore",
    "emerald_ore": "emerald_ore",
    "lapis_ore": "lapis_ore",
    "redstone_ore": "redstone_ore",
    "nether_quartz_ore": "quartz_ore",
    "nether_gold_ore": "nether_gold_ore",
    "ancient_debris": "ancient_debris",
    "gold_block": "gold_block",
    "iron_block": "iron_block",
    "diamond_block": "diamond_block",
    "emerald_block": "emerald_block",
    "netherite_block": "netherite_block",
    "lapis_block": "lapis_block",
    "redstone_block": "redstone_block",
    "coal_block": "coal_block",
    # 玻璃 / 玻璃板
    "glass": "glass",
    "glass_pane": "glass_pane",
    # 流体
    "water": "water",
    "lava": "lava",
    "obsidian": "obsidian",
    "crying_obsidian": "crying_obsidian",
    "glowstone": "glowstone",
    "sea_lantern": "sea_lantern",
    # 砖石类
    "bricks": "brick_block",
    "nether_bricks": "nether_brick",
    "red_nether_bricks": "red_nether_brick",
    "stone_bricks": "stonebrick",
    "mossy_stone_bricks": "stonebrick",
    "cracked_stone_bricks": "stonebrick",
    "chiseled_stone_bricks": "stonebrick",
    "quartz_block": "quartz_block",
    "purpur_block": "purpur_block",
    "end_stone": "end_stone",
    "end_stone_bricks": "end_bricks",
    "sandstone": "sandstone",
    "red_sandstone": "red_sandstone",
    "prismarine": "prismarine",
    "prismarine_bricks": "prismarine_bricks",
    "dark_prismarine": "dark_prismarine",
    # 羊毛 (16 色)
    "white_wool": "wool",
    "orange_wool": "wool",
    "magenta_wool": "wool",
    "light_blue_wool": "wool",
    "yellow_wool": "wool",
    "lime_wool": "wool",
    "pink_wool": "wool",
    "gray_wool": "wool",
    "light_gray_wool": "wool",
    "cyan_wool": "wool",
    "purple_wool": "wool",
    "blue_wool": "wool",
    "brown_wool": "wool",
    "green_wool": "wool",
    "red_wool": "wool",
    "black_wool": "wool",
    # 混凝土 (16 色)
    "white_concrete": "concrete",
    "orange_concrete": "concrete",
    "magenta_concrete": "concrete",
    "light_blue_concrete": "concrete",
    "yellow_concrete": "concrete",
    "lime_concrete": "concrete",
    "pink_concrete": "concrete",
    "gray_concrete": "concrete",
    "light_gray_concrete": "concrete",
    "cyan_concrete": "concrete",
    "purple_concrete": "concrete",
    "blue_concrete": "concrete",
    "brown_concrete": "concrete",
    "green_concrete": "concrete",
    "red_concrete": "concrete",
    "black_concrete": "concrete",
    # 陶土 / 带釉陶土
    "terracotta": "hardened_clay",
    "white_terracotta": "stained_hardened_clay",
    "orange_terracotta": "stained_hardened_clay",
    "magenta_terracotta": "stained_hardened_clay",
    "light_blue_terracotta": "stained_hardened_clay",
    "yellow_terracotta": "stained_hardened_clay",
    "lime_terracotta": "stained_hardened_clay",
    "pink_terracotta": "stained_hardened_clay",
    "gray_terracotta": "stained_hardened_clay",
    "light_gray_terracotta": "stained_hardened_clay",
    "cyan_terracotta": "stained_hardened_clay",
    "purple_terracotta": "stained_hardened_clay",
    "blue_terracotta": "stained_hardened_clay",
    "brown_terracotta": "stained_hardened_clay",
    "green_terracotta": "stained_hardened_clay",
    "red_terracotta": "stained_hardened_clay",
    "black_terracotta": "stained_hardened_clay",
    # 楼梯 / 台阶 / 栅栏 / 墙 (常见子集)
    "oak_stairs": "oak_stairs",
    "spruce_stairs": "spruce_stairs",
    "birch_stairs": "birch_stairs",
    "jungle_stairs": "jungle_stairs",
    "acacia_stairs": "acacia_stairs",
    "dark_oak_stairs": "dark_oak_stairs",
    "stone_stairs": "stone_stairs",
    "cobblestone_stairs": "stone_stairs",
    "brick_stairs": "brick_stairs",
    "stone_brick_stairs": "stone_brick_stairs",
    "nether_brick_stairs": "nether_brick_stairs",
    "sandstone_stairs": "sandstone_stairs",
    "red_sandstone_stairs": "red_sandstone_stairs",
    "quartz_stairs": "quartz_stairs",
    "purpur_stairs": "purpur_stairs",
    "prismarine_stairs": "prismarine_stairs",
    "oak_slab": "wooden_slab",
    "spruce_slab": "wooden_slab",
    "birch_slab": "wooden_slab",
    "jungle_slab": "wooden_slab",
    "acacia_slab": "wooden_slab",
    "dark_oak_slab": "wooden_slab",
    "stone_slab": "stone_slab",
    "cobblestone_slab": "stone_slab",
    "brick_slab": "stone_slab",
    "stone_brick_slab": "stone_slab",
    "nether_brick_slab": "stone_slab",
    "quartz_slab": "stone_slab",
    "oak_fence": "fence",
    "spruce_fence": "spruce_fence",
    "birch_fence": "birch_fence",
    "jungle_fence": "jungle_fence",
    "acacia_fence": "acacia_fence",
    "dark_oak_fence": "dark_oak_fence",
    "nether_brick_fence": "nether_brick_fence",
    "cobblestone_wall": "cobblestone_wall",
    "mossy_cobblestone_wall": "cobblestone_wall",
    "stone_brick_wall": "cobblestone_wall",
    "nether_brick_wall": "cobblestone_wall",
    # 杂项常见方块
    "stick": "stick",
    "torch": "torch",
    "crafting_table": "crafting_table",
    "furnace": "furnace",
    "chest": "chest",
    "bookshelf": "bookshelf",
    "tnt": "tnt",
    "jack_o_lantern": "lit_pumpkin",
    "pumpkin": "pumpkin",
    "melon": "melon_block",
    "sea_pickle": "sea_pickle",
    "beacon": "beacon",
    "anvil": "anvil",
    "enchanting_table": "enchanting_table",
    "brewing_stand": "brewing_stand",
    "cauldron": "cauldron",
    "hopper": "hopper",
    "dropper": "dropper",
    "dispenser": "dispenser",
    "note_block": "noteblock",
    "jukebox": "jukebox",
    "sponge": "sponge",
    "wet_sponge": "sponge",
    "netherrack": "netherrack",
    "soul_sand": "soul_sand",
    "soul_soil": "soul_soil",
    "magma_block": "magma",
    "cake": "cake",
    "ladder": "ladder",
    "iron_bars": "iron_bars",
    "vine": "vine",
    "cactus": "cactus",
    "piston": "piston",
    "sticky_piston": "sticky_piston",
    "rail": "rail",
    "powered_rail": "golden_rail",
    "detector_rail": "detector_rail",
    "activator_rail": "activator_rail",
    "lever": "lever",
    "stone_button": "stone_button",
    "oak_button": "wooden_button",
    "stone_pressure_plate": "stone_pressure_plate",
    "oak_pressure_plate": "wooden_pressure_plate",
    "redstone_wire": "redstone_wire",
    "redstone_torch": "redstone_torch",
    "redstone_lamp": "redstone_lamp",
    "repeater": "unpowered_repeater",
    "comparator": "unpowered_comparator",
    "observer": "observer",
    "daylight_detector": "daylight_detector",
    # 命令方块
    "command_block": "command_block",
    "chain_command_block": "chain_command_block",
    "repeating_command_block": "repeating_command_block",
    "structure_block": "structure_block",
    "structure_void": "structure_void",
    "jigsaw": "jigsaw",
    "barrier": "barrier",
    "light": "light_block",
    # 末地
    "end_portal_frame": "end_portal_frame",
    "end_portal": "end_portal",
    "end_rod": "end_rod",
    "chorus_plant": "chorus_plant",
    "chorus_flower": "chorus_flower",
    "purpur_pillar": "purpur_pillar",
    "shulker_box": "undyed_shulker_box",
    "dragon_egg": "dragon_egg",
}


# ---------------------------------------------------------------------------
# 4. 像素画方块颜色映射 / pixelart block color mapping
#    (r, g, b) -> "minecraft:xxx", 用于将图像像素转换为最接近的方块.
#    颜色为方块主色调近似值 (基于 Minecraft 平均色).
# ---------------------------------------------------------------------------
PIXELART_BLOCKS = {
    # ---- 16 色羊毛 ----
    (233, 236, 236): "minecraft:white_wool",
    (240, 118, 19): "minecraft:orange_wool",
    (189, 68, 179): "minecraft:magenta_wool",
    (58, 175, 217): "minecraft:light_blue_wool",
    (248, 198, 39): "minecraft:yellow_wool",
    (112, 185, 25): "minecraft:lime_wool",
    (237, 141, 172): "minecraft:pink_wool",
    (62, 68, 71): "minecraft:gray_wool",
    (142, 142, 134): "minecraft:light_gray_wool",
    (21, 119, 136): "minecraft:cyan_wool",
    (126, 52, 161): "minecraft:purple_wool",
    (53, 57, 157): "minecraft:blue_wool",
    (86, 51, 28): "minecraft:brown_wool",
    (54, 75, 24): "minecraft:green_wool",
    (161, 39, 34): "minecraft:red_wool",
    (21, 22, 26): "minecraft:black_wool",
    # ---- 16 色混凝土 ----
    (207, 213, 214): "minecraft:white_concrete",
    (236, 128, 21): "minecraft:orange_concrete",
    (179, 55, 161): "minecraft:magenta_concrete",
    (50, 158, 217): "minecraft:light_blue_concrete",
    (242, 175, 22): "minecraft:yellow_concrete",
    (109, 169, 24): "minecraft:lime_concrete",
    (226, 132, 159): "minecraft:pink_concrete",
    (58, 62, 66): "minecraft:gray_concrete",
    (130, 130, 130): "minecraft:light_gray_concrete",
    (16, 100, 122): "minecraft:cyan_concrete",
    (113, 41, 145): "minecraft:purple_concrete",
    (44, 47, 143): "minecraft:blue_concrete",
    (74, 44, 24): "minecraft:brown_concrete",
    (50, 67, 19): "minecraft:green_concrete",
    (158, 31, 25): "minecraft:red_concrete",
    (19, 20, 22): "minecraft:black_concrete",
    # ---- 16 色陶土 ----
    (209, 177, 161): "minecraft:white_terracotta",
    (167, 99, 39): "minecraft:orange_terracotta",
    (146, 60, 98): "minecraft:magenta_terracotta",
    (99, 110, 141): "minecraft:light_blue_terracotta",
    (186, 133, 35): "minecraft:yellow_terracotta",
    (84, 99, 38): "minecraft:lime_terracotta",
    (167, 80, 78): "minecraft:pink_terracotta",
    (58, 42, 36): "minecraft:gray_terracotta",
    (135, 107, 98): "minecraft:light_gray_terracotta",
    (86, 65, 64): "minecraft:cyan_terracotta",
    (113, 56, 80): "minecraft:purple_terracotta",
    (73, 60, 89): "minecraft:blue_terracotta",
    (78, 53, 36): "minecraft:brown_terracotta",
    (76, 83, 41): "minecraft:green_terracotta",
    (149, 60, 43): "minecraft:red_terracotta",
    (37, 23, 16): "minecraft:black_terracotta",
    # ---- 16 色带釉陶土 ----
    (137, 176, 158): "minecraft:white_glazed_terracotta",
    (208, 132, 65): "minecraft:orange_glazed_terracotta",
    (199, 126, 178): "minecraft:magenta_glazed_terracotta",
    (106, 161, 191): "minecraft:light_blue_glazed_terracotta",
    (220, 182, 73): "minecraft:yellow_glazed_terracotta",
    (126, 184, 88): "minecraft:lime_glazed_terracotta",
    (209, 132, 152): "minecraft:pink_glazed_terracotta",
    (80, 86, 87): "minecraft:gray_glazed_terracotta",
    (157, 157, 149): "minecraft:light_gray_glazed_terracotta",
    (88, 123, 124): "minecraft:cyan_glazed_terracotta",
    (155, 110, 162): "minecraft:purple_glazed_terracotta",
    (89, 94, 162): "minecraft:blue_glazed_terracotta",
    (106, 79, 60): "minecraft:brown_glazed_terracotta",
    (99, 116, 73): "minecraft:green_glazed_terracotta",
    (167, 82, 71): "minecraft:red_glazed_terracotta",
    (42, 35, 38): "minecraft:black_glazed_terracotta",
    # ---- 16 色染色玻璃 ----
    (208, 213, 214): "minecraft:white_stained_glass",
    (240, 155, 57): "minecraft:orange_stained_glass",
    (199, 78, 189): "minecraft:magenta_stained_glass",
    (58, 175, 217): "minecraft:light_blue_stained_glass",
    (249, 214, 57): "minecraft:yellow_stained_glass",
    (127, 204, 25): "minecraft:lime_stained_glass",
    (237, 141, 172): "minecraft:pink_stained_glass",
    (65, 70, 73): "minecraft:gray_stained_glass",
    (154, 161, 161): "minecraft:light_gray_stained_glass",
    (37, 142, 158): "minecraft:cyan_stained_glass",
    (137, 50, 179): "minecraft:purple_stained_glass",
    (53, 57, 157): "minecraft:blue_stained_glass",
    (97, 64, 36): "minecraft:brown_stained_glass",
    (76, 110, 32): "minecraft:green_stained_glass",
    (161, 39, 34): "minecraft:red_stained_glass",
    (25, 25, 31): "minecraft:black_stained_glass",
    # ---- 自然 / 特殊方块 ----
    (200, 90, 50): "minecraft:red_sand",            # 红沙
    (197, 175, 75): "minecraft:sand",               # 沙子
    (165, 105, 25): "minecraft:jack_o_lantern",     # 南瓜灯
    (255, 165, 30): "minecraft:pumpkin",            # 南瓜
    (220, 220, 220): "minecraft:sea_lantern",       # 海晶灯
    (137, 116, 69): "minecraft:glowstone",          # 萤石
    (25, 50, 160): "minecraft:lapis_block",         # 青金石块
    (17, 124, 79): "minecraft:emerald_block",       # 祖母绿块
    (220, 220, 222): "minecraft:iron_block",        # 铁块
    (250, 235, 80): "minecraft:gold_block",         # 金块
    (123, 235, 235): "minecraft:diamond_block",     # 钻石块
    (45, 40, 45): "minecraft:netherite_block",      # 下界合金块
    (135, 30, 25): "minecraft:redstone_block",      # 红石块
    (89, 119, 100): "minecraft:prismarine",         # 海晶石
    (110, 130, 90): "minecraft:prismarine_bricks",  # 海晶石砖
    (60, 80, 70): "minecraft:dark_prismarine",      # 暗海晶石
    (15, 12, 30): "minecraft:obsidian",             # 黑曜石
    (130, 30, 60): "minecraft:netherrack",          # 下界岩
    (90, 70, 60): "minecraft:soul_sand",            # 灵魂沙
    (124, 124, 124): "minecraft:stone",             # 石头
    (120, 120, 120): "minecraft:cobblestone",       # 圆石
    (90, 60, 35): "minecraft:oak_log",              # 橡木原木
    (160, 130, 80): "minecraft:oak_planks",         # 橡木木板
    (110, 140, 70): "minecraft:oak_leaves",         # 橡树叶
    (95, 70, 50): "minecraft:dirt",                 # 泥土
    (180, 180, 180): "minecraft:quartz_block",      # 石英块
    (160, 110, 110): "minecraft:purpur_block",      # 紫珀块
    (210, 200, 190): "minecraft:end_stone",         # 末地石
    (160, 160, 160): "minecraft:terracotta",        # 陶土
    (50, 90, 130): "minecraft:water",               # 水
    (180, 70, 30): "minecraft:lava",                # 岩浆
    (245, 245, 245): "minecraft:snow_block",        # 雪块
    (170, 200, 230): "minecraft:ice",               # 冰
    (120, 160, 200): "minecraft:packed_ice",        # 浮冰
    (70, 110, 170): "minecraft:blue_ice",           # 蓝冰
    (90, 70, 35): "minecraft:bricks",               # 砖块
    (60, 40, 40): "minecraft:nether_bricks",        # 下界砖
    (170, 130, 80): "minecraft:sandstone",          # 砂岩
    (120, 70, 50): "minecraft:red_sandstone",       # 红砂岩
    (40, 40, 40): "minecraft:bedrock",              # 基岩
    (215, 215, 215): "minecraft:white_wool",        # 备用白
}


# ---------------------------------------------------------------------------
# 5. 颜色匹配辅助函数 / color matching helpers
# ---------------------------------------------------------------------------
def _squared_distance(c1, c2):
    """计算 RGB 平方距离 (不开方以提速)."""
    dr = c1[0] - c2[0]
    dg = c1[1] - c2[1]
    db = c1[2] - c2[2]
    return dr * dr + dg * dg + db * db


def find_closest_block(r, g, b, palette=None):
    """在颜色表中找到与 (r, g, b) 最接近的方块.

    Args:
        r, g, b: 0-255 整数颜色分量.
        palette: 可选的 { (r,g,b): "minecraft:xxx" } 字典, 默认使用 PIXELART_BLOCKS.

    Returns:
        str: 最接近方块的 "minecraft:xxx" 名称; 调色板为空时返回 None.
    """
    if palette is None:
        palette = PIXELART_BLOCKS
    if not palette:
        return None
    target = (r, g, b)
    best_name = None
    best_dist = None
    for color, name in palette.items():
        dist = _squared_distance(color, target)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def get_block_id(name):
    """根据方块名获取 Bedrock 数字 ID.

    支持带或不带 "minecraft:" 前缀. 未匹配返回 0 (air / 未知).

    Args:
        name: 方块名, 如 "stone" 或 "minecraft:stone".

    Returns:
        int: Bedrock 数字 ID; 未知方块返回 0.
    """
    if not name:
        return 0
    # 规范化名称: 去前缀, 去空白
    key = name.strip().lower()
    if key.startswith("minecraft:"):
        key = key[len("minecraft:"):]
    return _NAME_TO_ID.get(key, 0)


# ---------------------------------------------------------------------------
# 6. Bedrock 数字 ID -> 名称映射 / Bedrock numeric block id map
#    key = 数字 ID (legacy runtime id 0-201), value = Bedrock 方块名
#    (不含 minecraft: 前缀; 现代版本新增方块使用字符串标识, 不在此表)
#    涵盖原版主世界 / 下界 / 末地常用方块, 共 202 条.
# ---------------------------------------------------------------------------
BEDROCK_BLOCK_IDS = {
    # --- 空气与基础 (0-11) ---
    0: "air",
    1: "stone",
    2: "grass",
    3: "dirt",
    4: "cobblestone",
    5: "planks",
    6: "sapling",
    7: "bedrock",
    8: "flowing_water",
    9: "water",
    10: "flowing_lava",
    11: "lava",
    # --- 沙石/矿物 (12-22) ---
    12: "sand",
    13: "gravel",
    14: "gold_ore",
    15: "iron_ore",
    16: "coal_ore",
    17: "log",
    18: "leaves",
    19: "sponge",
    20: "glass",
    21: "lapis_ore",
    22: "lapis_block",
    # --- 功能方块 (23-44) ---
    23: "dispenser",
    24: "sandstone",
    25: "noteblock",
    26: "bed",
    27: "golden_rail",
    28: "detector_rail",
    29: "sticky_piston",
    30: "web",
    31: "tallgrass",
    32: "deadbush",
    33: "piston",
    34: "piston_arm_collision",
    35: "wool",
    36: "element_0",
    37: "yellow_flower",
    38: "red_flower",
    39: "brown_mushroom",
    40: "red_mushroom",
    41: "gold_block",
    42: "iron_block",
    43: "double_stone_slab",
    44: "stone_slab",
    # --- 砖石/红石 (45-78) ---
    45: "brick_block",
    46: "tnt",
    47: "bookshelf",
    48: "mossy_cobblestone",
    49: "obsidian",
    50: "torch",
    51: "fire",
    52: "mob_spawner",
    53: "oak_stairs",
    54: "chest",
    55: "redstone_wire",
    56: "diamond_ore",
    57: "diamond_block",
    58: "crafting_table",
    59: "wheat",
    60: "farmland",
    61: "furnace",
    62: "lit_furnace",
    63: "standing_sign",
    64: "wooden_door",
    65: "ladder",
    66: "rail",
    67: "stone_stairs",
    68: "wall_sign",
    69: "lever",
    70: "stone_pressure_plate",
    71: "iron_door",
    72: "wooden_pressure_plate",
    73: "redstone_ore",
    74: "lit_redstone_ore",
    75: "unlit_redstone_torch",
    76: "redstone_torch",
    77: "stone_button",
    78: "snow_layer",
    # --- 冰雪/植物/装饰 (79-97) ---
    79: "ice",
    80: "snow",
    81: "cactus",
    82: "clay",
    83: "reeds",
    84: "jukebox",
    85: "fence",
    86: "pumpkin",
    87: "netherrack",
    88: "soul_sand",
    89: "glowstone",
    90: "portal",
    91: "lit_pumpkin",
    92: "cake",
    93: "unpowered_repeater",
    94: "powered_repeater",
    95: "invisible_bedrock",
    96: "trapdoor",
    97: "monster_egg",
    # --- 石砖/末地 (98-126) ---
    98: "stonebrick",
    99: "brown_mushroom_block",
    100: "red_mushroom_block",
    101: "iron_bars",
    102: "glass_pane",
    103: "melon_block",
    104: "pumpkin_stem",
    105: "melon_stem",
    106: "vine",
    107: "fence_gate",
    108: "brick_stairs",
    109: "stone_brick_stairs",
    110: "mycelium",
    111: "waterlily",
    112: "nether_brick",
    113: "nether_brick_fence",
    114: "nether_brick_stairs",
    115: "nether_wart",
    116: "enchanting_table",
    117: "brewing_stand",
    118: "cauldron",
    119: "end_portal",
    120: "end_portal_frame",
    121: "end_stone",
    122: "dragon_egg",
    123: "redstone_lamp",
    124: "lit_redstone_lamp",
    125: "double_wooden_slab",
    126: "wooden_slab",
    # --- 1.4-1.7 方块 (127-165) ---
    127: "cocoa",
    128: "sandstone_stairs",
    129: "emerald_ore",
    130: "ender_chest",
    131: "tripwire_hook",
    132: "tripwire",
    133: "emerald_block",
    134: "spruce_stairs",
    135: "birch_stairs",
    136: "jungle_stairs",
    137: "command_block",
    138: "beacon",
    139: "cobblestone_wall",
    140: "flower_pot",
    141: "carrots",
    142: "potatoes",
    143: "wooden_button",
    144: "skull",
    145: "anvil",
    146: "trapped_chest",
    147: "light_weighted_pressure_plate",
    148: "heavy_weighted_pressure_plate",
    149: "unpowered_comparator",
    150: "powered_comparator",
    151: "daylight_detector",
    152: "redstone_block",
    153: "quartz_ore",
    154: "hopper",
    155: "quartz_block",
    156: "quartz_stairs",
    157: "activator_rail",
    158: "dropper",
    159: "stained_hardened_clay",
    160: "stained_glass_pane",
    161: "leaves2",
    162: "log2",
    163: "acacia_stairs",
    164: "dark_oak_stairs",
    165: "slime",
    # --- 1.8-1.10 方块 (166-201) ---
    166: "barrier",
    167: "iron_trapdoor",
    168: "prismarine",
    169: "sea_lantern",
    170: "hay_bale",
    171: "carpet",
    172: "hardened_clay",
    173: "coal_block",
    174: "packed_ice",
    175: "double_plant",
    176: "standing_banner",
    177: "wall_banner",
    178: "daylight_detector_inverted",
    179: "red_sandstone",
    180: "red_sandstone_stairs",
    181: "double_stone_slab2",
    182: "stone_slab2",
    183: "spruce_fence_gate",
    184: "birch_fence_gate",
    185: "jungle_fence_gate",
    186: "dark_oak_fence_gate",
    187: "acacia_fence_gate",
    188: "spruce_fence",
    189: "birch_fence",
    190: "jungle_fence",
    191: "dark_oak_fence",
    192: "acacia_fence",
    193: "spruce_door",
    194: "birch_door",
    195: "jungle_door",
    196: "acacia_door",
    197: "dark_oak_door",
    198: "end_rod",
    199: "chorus_plant",
    200: "chorus_flower",
    201: "purpur_block",
}


# 名称 -> ID 反向查找表 (内部使用, 由 BEDROCK_BLOCK_IDS 构建)
_NAME_TO_ID = {}
for _id, _name in BEDROCK_BLOCK_IDS.items():
    _NAME_TO_ID.setdefault(_name, _id)
