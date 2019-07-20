from enum import Enum
from .pieces import *


class KeyMappings(Enum):
    """Represents key-map binding values to be used for the Player class's key_mapping dictionary"""
    SHIFT_RIGHT = 0
    SHIFT_LEFT = 1
    ROTATE = 2
    SOFT_DROP = 3
    DROP = 4


def int_to_block(i: int, x_pos, y_pos) -> Block:
    if i == 0:
        return TBlock(x_pos, y_pos)
    elif i == 1:
        return OBlock(x_pos, y_pos)
    elif i == 2:
        return IBlock(x_pos, y_pos)
    elif i == 3:
        return LBlock(x_pos, y_pos)
    elif i == 4:
        return JBlock(x_pos, y_pos)
    elif i == 5:
        return SBlock(x_pos, y_pos)
    elif i == 6:
        return ZBlock(x_pos, y_pos)


def iteration_delay(level: int) -> float:
    """Determines the iteration delay in seconds given the current level"""
    if level == 1:
        return 0.5
    elif level == 2:
        return 0.45
    elif level == 3:
        return 0.4
    elif level == 4:
        return 0.35
    elif level == 5:
        return 0.3
    elif level == 6:
        return 0.25
    elif level == 7:
        return 0.2
    elif level == 8:
        return 0.15
    elif level == 9:
        return 0.1
    elif level >= 10:
        return 0.05


def get_score_points(level: int, num_lines: int, dropped_grids: int = 0, hard: bool = False) -> int:
    """Determines how many points to award when lines are cleared"""

    mult = level + 1
    temp = 0

    if num_lines == 1:
        temp = 40
    elif num_lines == 2:
        temp = 100
    elif num_lines == 3:
        temp = 300
    elif num_lines == 4:
        temp = 1200

    return temp * mult + (dropped_grids * (1 if not hard else 2))

