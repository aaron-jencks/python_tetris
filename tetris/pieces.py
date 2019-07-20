import curses
import numpy as np


class Block:
    """Defines the class for a tetris piece, each piece contains 4 squares,
    the color and style and shape can be defined here"""

    def __init__(self, pos_x: int, pos_y: int):
        self.offset = (pos_x, pos_y)
        self.num = -1

        self.color = curses.COLOR_WHITE
        self.pair_initialized = False
        self.pair_index = 0
        self.symbol = '\u2592'

        self.rotation = 0
        self.max_rotation = 0

        self.locations = np.zeros(shape=(4, 4), dtype=int)

        self.create_locations()

    def init_color_pair(self, index: int = 1):
        curses.init_pair(index, self.color, self.color)
        self.pair_initialized = True
        self.pair_index = index

    def create_locations(self):
        """Generates the location arrays based on the rotation value"""
        # resets the locations
        for i in range(4):
            for j in range(4):
                self.locations[i, j] = 0

    # region Movement

    def __shift(self, left: bool):
        """Shifts the block either left or right, depending on the arguments and available space."""
        # TODO Check collisions here (I check for collision on the board, not here)
        x, y = self.offset
        if left:
            self.offset = (x - 1, y)
        else:
            self.offset = (x + 1, y)

    def right(self):
        """Shifts the current piece 1 space to the right"""
        self.__shift(False)

    def left(self):
        """Shifts the current piece 1 space to the left"""
        self.__shift(True)

    def rotate(self, clockwise: bool = False):
        """Rotates the piece 90 degrees counter-clockwise, or clockwise, depending on the boolean"""
        if clockwise:
            self.rotation -= 1
        else:
            self.rotation += 1

        if self.rotation >= self.max_rotation:
            self.rotation = 0
        elif self.rotation < 0:
            self.rotation = self.max_rotation - 1

        self.create_locations()

    def descend(self, lines: int = 1):
        """Drops the block by the number of lines provided, default is 1"""
        x, y = self.offset
        self.offset = (x, y + lines)

    # endregion

    def __str__(self):

        result = ""
        for i in range(4):
            for j in range(4):
                result += ' ' if self.locations[i, j] != 1 else self.symbol
            result += '\n'

        return result[:-1]

    def add_to_screen(self, screen):
        x, y = self.offset

        for i in range(4):
            for j in range(4):
                if self.locations[i, j] != 0:
                    screen.addstr(y + i, x + j, self.symbol, curses.color_pair(self.pair_index))


class TBlock(Block):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y)
        self.color = curses.COLOR_YELLOW
        # self.init_color_pair(1)
        self.max_rotation = 4
        self.num = 0

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[1, 1] = 1
            self.locations[1, 2] = 1
            self.locations[1, 3] = 1
            self.locations[2, 2] = 1
        elif self.rotation == 1:
            self.locations[2, 1] = 1
            self.locations[2, 0] = 1
            self.locations[3, 1] = 1
            self.locations[2, 2] = 1
        elif self.rotation == 2:
            self.locations[1, 1] = 1
            self.locations[1, 2] = 1
            self.locations[1, 3] = 1
            self.locations[2, 0] = 1
        elif self.rotation == 3:
            self.locations[1, 1] = 1
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1


class OBlock(Block):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y)
        self.color = curses.COLOR_BLUE
        # self.init_color_pair(2)
        self.max_rotation = 1
        self.num = 1

    def create_locations(self):
        super().create_locations()

        self.locations[1, 1] = 1
        self.locations[2, 2] = 1
        self.locations[2, 1] = 1
        self.locations[1, 2] = 1


class IBlock(Block):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y)
        self.color = curses.COLOR_RED
        # self.init_color_pair(3)
        self.max_rotation = 2
        self.num = 2

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[0, 0] = 1
            self.locations[0, 1] = 1
            self.locations[0, 2] = 1
            self.locations[0, 3] = 1
        elif self.rotation == 1:
            self.locations[0, 2] = 1
            self.locations[1, 2] = 1
            self.locations[2, 2] = 1
            self.locations[3, 2] = 1


# region Isomers

class IsomerBlock(Block):
    """The L-shaped blocks, use mirrored for right one"""
    def __init__(self, pos_x: int, pos_y: int, mirrored: bool = False):
        super().__init__(pos_x, pos_y)
        self.mirrored = mirrored
        self.max_rotation = 4


class LBlock(IsomerBlock):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y)
        self.color = curses.COLOR_WHITE
        # self.init_color_pair(4)
        self.num = 3

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[1, 1] = 1
            self.locations[1, 2] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
        elif self.rotation == 1:
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1
            self.locations[3, 2] = 1
        elif self.rotation == 2:
            self.locations[1, 1] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
            self.locations[3, 0] = 1
        elif self.rotation == 3:
            self.locations[1, 0] = 1
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1


class JBlock(IsomerBlock):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y, True)
        self.color = curses.COLOR_MAGENTA
        # self.init_color_pair(5)
        self.num = 4

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[1, 1] = 1
            self.locations[3, 2] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
        elif self.rotation == 1:
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1
            self.locations[3, 0] = 1
        elif self.rotation == 2:
            self.locations[1, 1] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
            self.locations[1, 0] = 1
        elif self.rotation == 3:
            self.locations[1, 2] = 1
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1

# endregion


# region Dog Blocks

class ZigZagBlock(Block):
    """The L-shaped blocks, use mirrored for right one"""

    def __init__(self, pos_x: int, pos_y: int, mirrored: bool = False):
        super().__init__(pos_x, pos_y)
        self.mirrored = mirrored
        self.max_rotation = 2


class SBlock(ZigZagBlock):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y)
        self.color = curses.COLOR_CYAN
        # self.init_color_pair(6)
        self.num = 5

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[1, 2] = 1
            self.locations[2, 2] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
        elif self.rotation == 1:
            self.locations[2, 0] = 1
            self.locations[2, 1] = 1
            self.locations[3, 1] = 1
            self.locations[3, 2] = 1


class ZBlock(ZigZagBlock):
    def __init__(self, pos_x: int, pos_y: int):
        super().__init__(pos_x, pos_y, True)
        self.color = curses.COLOR_GREEN
        # self.init_color_pair(7)
        self.num = 6

    def create_locations(self):
        super().create_locations()

        if self.rotation == 0:
            self.locations[1, 1] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1
            self.locations[3, 2] = 1
        elif self.rotation == 1:
            self.locations[3, 0] = 1
            self.locations[3, 1] = 1
            self.locations[2, 1] = 1
            self.locations[2, 2] = 1

# endregion
