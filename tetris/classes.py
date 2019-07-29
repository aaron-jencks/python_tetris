import numpy as np
import json
import random
import time
from copy import deepcopy
import pygame

from display_util.string_display_util import boxed_text, hstack, control_arrows
from display_util.menu import add_multiline_string
from .shared import int_to_block, KeyMappings, iteration_delay
from .input.gamepad import GamePadButtonEventData, GamePadHatEventData, HatPositionType, GamePadEventData


pygame.init()
if not pygame.joystick.get_init():
    pygame.joystick.init()

pgj = pygame.joystick


class Board:
    """Contains a numpy array that holds the blocks for the game, contains methods for descent, dropping, and moving."""

    def __init__(self, pos_x: int, pos_y: int, piece_callback, width: int = 10, height: int = 20, scale: int = 1):
        self.offset = (pos_x, pos_y)
        self.scale = scale
        self.width = width
        self.width_total = width * scale
        self.height = height
        self.height_total = height * scale
        self.pieces = []
        self.current_piece = None
        self.grid = np.zeros(shape=(width, height), dtype=int)
        self.background_char = '\u2591'
        self.read_for_piece = True
        self.piece_callback = piece_callback

        self.level = 1
        self.lines = 0
        self.score = 0

        self.delay = iteration_delay(self.level)
        self.time_start = time.time()

        self.playing = True

    def reset(self):
        self.pieces = []
        self.current_piece = None
        self.grid = np.zeros(shape=(self.width, self.height), dtype=int)

        self.read_for_piece = True

        self.level = 1
        self.lines = 0
        self.score = 0

        self.delay = iteration_delay(self.level)
        self.time_start = time.time()

        self.playing = True

    def lose(self):
        """Ends the game for this board"""
        self.playing = False

    def __get_existing_board(self) -> np.ndarray:
        """Returns an array containing pieces for all pieces except the current one, used to determine valid
        rotations and movements."""

        result = np.zeros(shape=(self.width, self.height), dtype=int)

        x_t, y_t = self.offset

        # All of these pieces should already be in legal positions
        for p in self.pieces:
            x, y = p.offset
            x -= x_t
            y -= y_t

            for i in range(y, y + 4):
                for j in range(x, x + 4):
                    if p.locations[i - y, j - x] != 0:
                        result[j, i] = p.num

        return result

    def update_grid(self) -> bool:
        """Takes the locations of all of the pieces and places them into the board's grid,
        reutrns whether the player is in a legal position or not"""

        x_t, y_t = self.offset

        self.grid = self.__get_existing_board()

        if self.current_piece is not None:
            x, y = self.current_piece.offset
            x -= x_t
            y -= y_t

            for i in range(y, y + 4):
                for j in range(x, x + 4):
                    if self.current_piece.locations[i - y, j - x] != 0:
                        if self.grid[j, i] == 0:
                            self.grid[j, i] = self.current_piece.num
                        else:
                            return False

        return True

    @property
    def ready_update(self):
        return time.time() - self.time_start >= self.delay

    def update(self):
        if self.playing and self.ready_update:
            if self.read_for_piece:
                self.piece_callback()
            else:
                if not self.descend():
                    self.place_piece()

                self.time_start = time.time()
                if not self.update_grid():
                    self.lose()
                # TODO Handle updating level and score and shit

    def new_piece(self, identifier: int):
        """Puts a new piece onto the board."""
        self.current_piece = int_to_block(identifier, self.offset[0] + 4, self.offset[1] + 1)
        self.read_for_piece = False

        # Resets the time interval
        self.time_start = time.time()

    def place_piece(self):
        """Freezes the current piece where it's at and adds it to the pieces list, then generatesa a new piece"""

        # Freezes the current piece
        self.pieces.append(self.current_piece)
        self.read_for_piece = True

        # Generates a new piece
        self.piece_callback()

        # Resets the time interval
        self.time_start = time.time()

    # region Display Functions

    def get_board_string(self) -> str:
        """Creates a string representation of the current board start"""
        width, height = self.grid.shape
        body = ""

        for i in range(height):
            for _ in range(self.scale):
                for j in range(width):
                    n = self.grid[j, i]
                    if n > 0:
                        n_b = int_to_block(n, 0, 0)
                        char = n_b.symbol
                    else:
                        char = self.background_char
                    body += char * self.scale
                body += '\n'

        return boxed_text(body[:-1]) + '\n'

    def get_game_over_string(self) -> str:
        """Creates a string that notifies the user of the end of their game."""

        return boxed_text("Game Over!\nLevel: {}\nLines: {}\nScore: {}".format(self.level,
                                                                               self.lines,
                                                                               self.score))

    def __str__(self):
        """Returns a string containing this board's grid"""

        result = self.get_board_string()

        if not self.playing:
            gos = self.get_game_over_string()

            w = max([len(s) for s in gos.splitlines(False)])
            diff = self.width_total - w
            if diff < 0:
                diff = 0
            diff = diff // 2

            for line in gos.splitlines(True):
                result += " " * diff + line

        return result

    def add_to_screen(self, screen):
        """Prints the tetris board out to the screen"""
        x, y = self.offset

        add_multiline_string(self.get_board_string(), screen, x, y, False)

        if not self.playing:
            gos = self.get_game_over_string()

            w = max([len(s) for s in gos.splitlines(False)])
            diff = self.width_total - w
            if diff < 0:
                diff = 0
            diff = diff // 2

            add_multiline_string(gos, screen, x + diff, y + (self.height_total // 2), False)

    # endregion

    # region Piece class wrapper

    def __inside_board(self, x: int = 0, y: int = 0) -> bool:
        """Determines if the given coordinate exists inside of the board's space, or if it's outside of the region"""
        return 0 <= x < self.width and 0 <= y < self.height

    # region Shifting

    @property
    def can_shift_right(self) -> bool:
        if self.current_piece is not None:
            x, y = self.current_piece.offset
            xt, yt = self.offset
            x -= xt
            y -= yt

            temp_grid = self.__get_existing_board()

            for i in range(4):
                for j in range(4):
                    if self.current_piece.locations[i, j] != 0:
                        temp = x + j + 1
                        if not self.__inside_board(temp) or temp_grid[temp, y + i] != 0:
                            return False
            return True
        return False

    def right(self) -> bool:
        """Shifts the current piece right, returns True, if the piece was moved,
        does not move the piece if it is against the wall"""
        if self.can_shift_right:
            self.current_piece.right()
            self.update_grid()
            return True
        return False

    @property
    def can_shift_left(self) -> bool:
        if self.current_piece is not None:
            x, y = self.current_piece.offset
            xt, yt = self.offset
            x -= xt
            y -= yt

            temp_grid = self.__get_existing_board()

            for i in range(4):
                for j in range(4):
                    if self.current_piece.locations[i, j] != 0:
                        temp = x + j - 1
                        if not self.__inside_board(temp) or temp_grid[temp, y + i] != 0:
                            return False
            return True
        return False

    def left(self) -> bool:
        """Shifts the current piece left, returns True if the piece was moved,
        does not move the piece if it is against the wall"""
        if self.can_shift_left:
            self.current_piece.left()
            self.update_grid()
            return True
        return False

    # endregion

    # region Rotation

    @property
    def can_rotate(self) -> bool:
        # TODO Could probably be a bit more efficient

        if self.current_piece is not None:
            x, y = self.current_piece.offset
            xt, yt = self.offset
            x -= xt
            y -= yt

            # Tries rotating the piece first
            self.current_piece.rotate()

            # Checks if the piece overlaps with any of the existing pieces
            # Checks if the piece is still on the board
            temp_grid = self.__get_existing_board()
            result = True
            for i in range(4):
                for j in range(4):
                    if self.current_piece.locations[i, j] != 0:
                        temp_x = x + j
                        temp_y = y + i
                        if not self.__inside_board(temp_x, temp_y) or temp_grid[temp_x, temp_y] != 0:
                            result = False

            # Undoes the rotation
            self.current_piece.rotate(True)

            return result
        return False

    def rotate(self) -> bool:
        """Rotates the current piece, returns True if the piece was rotated,
        does not rotate is doing so would invalidate the piece"""
        if self.current_piece is not None:
            self.current_piece.rotate()
            self.update_grid()
            return True
        return False

    # endregion

    # region Descent

    @property
    def can_descend(self) -> bool:
        if self.current_piece is not None:
            x, y = self.current_piece.offset
            xt, yt = self.offset
            x -= xt
            y -= yt

            temp_grid = self.__get_existing_board()

            for i in range(4):
                for j in range(4):
                    if self.current_piece.locations[i, j] != 0:
                        temp = y + i + 1
                        if not self.__inside_board(0, temp) or temp_grid[x + j, temp] != 0:
                            return False
            return True
        return False

    def descend(self) -> bool:
        """Moves the current piece down one row, if possible"""
        if self.can_descend:
            self.current_piece.descend()
            self.update_grid()
            return True
        return False

    # region Drops

    def __min_drop_distance(self) -> int:
        """Finds the minimum amount of distance the current piece would need to descend to be considered placed.
        :returns -1 if self.current_piece is None, or if the piece is alredy placed,
         otherwise, the minimum distance to consider the piece placed."""

        if self.current_piece is not None:
            x_t, y_t = self.current_piece.offset

            distances = []

            temp_grid = self.__get_existing_board()

            exposed = []

            # Determines the locations on the piece that are exposed on the bottom
            for i in range(4):
                for j in range(4):
                    if self.current_piece.locations[i, j] != 0:
                        if i < 3 and self.current_piece.locations[i + 1, j] == 0:
                            exposed.append((i, j))
                        elif i == 3:
                            exposed.append((i, j))

            # Calculates the distances that the piece would have to travel at each of those locations to hit something
            for y, x in exposed:
                act_x = x + x_t
                act_y = y + y_t

                current = act_y
                while current < self.height and temp_grid[act_x, current] == 0:
                    current += 1

                # We can break early if we determine that the piece cannot be dropped at all
                if current - act_y - 1 < 0:
                    return -1

                distances.append(current - act_y - 1)

            return min(distances)
        return -1

    def drop(self):
        """Drops the current piece down to the nearest location it can go"""
        self.current_piece.descend(self.__min_drop_distance())
        self.place_piece()
        self.update_grid()

    def soft_drop(self):
        """Performs a soft drop of the current piece"""
        if not self.descend():
            self.place_piece()
        self.update_grid()

    # endregion

    # endregion

    # endregion


class Player:
    """Represents a player, contains a queue for collected user input and
    a list of valid keys that the player can accept"""

    def __init__(self, joystick: int, key_mapping: dict, board: Board):
        self.joystick = joystick
        self.keys = key_mapping
        self.board = board

    def __contains__(self, item):
        """Determines if an event is registered on this controller, or if a KeyMapping has a mapped function"""
        if isinstance(item, GamePadEventData):
            for v in self.keys.values():
                if item == v:
                    return True
            return False
        elif isinstance(item, KeyMappings):
            for k in self.keys:
                if k == item:
                    return True
            return False
        elif isinstance(item, int):
            return item == self.joystick
        return False

    def get_function(self, function: KeyMappings):
        """Returns the mapped function for the given KeyMapping command"""
        if function == KeyMappings.DROP:
            return self.board.drop
        elif function == KeyMappings.SOFT_DROP:
            return self.board.soft_drop
        elif function == KeyMappings.ROTATE:
            return self.board.rotate
        elif function == KeyMappings.SHIFT_LEFT:
            return self.board.left
        elif function == KeyMappings.SHIFT_RIGHT:
            return self.board.right


class Tetris:
    """Contains the functions to run a game of tetris, these include holding the grid values, terminal location, and
    scores and such..."""

    def __init__(self, pos_x: int, pos_y: int, num_players: int = 1,
                 board_width: int = 10, board_height: int = 20, scale: int = 1):
        self.offset = (pos_x, pos_y)

        self.scale = scale
        self.board_width = board_width
        self.board_width_adj = board_width * scale + 2
        self.board_width_total = num_players * self.board_width_adj
        self.board_height = board_height
        self.board_height_total = board_height * scale + 2

        self.highscore = 0
        self.next_piece = -1

        self.boards = []
        for i in range(num_players):
            x = pos_x + self.board_width_adj * i
            self.boards.append(Board(x, pos_y, self.gen_next_piece,
                                     board_width, board_height, scale))

        player_keymappings = {KeyMappings.SHIFT_LEFT: GamePadHatEventData(0, HatPositionType.LEFT, True),
                              KeyMappings.SOFT_DROP: GamePadHatEventData(0, HatPositionType.DOWN, False),
                              KeyMappings.SHIFT_RIGHT: GamePadHatEventData(0, HatPositionType.RIGHT, True),
                              KeyMappings.ROTATE: GamePadButtonEventData(0, False),
                              KeyMappings.DROP: GamePadButtonEventData(3, False)}

        if num_players > pgj.get_count():
            raise AssertionError("You can't have more players than you have controllers, silly!")

        self.players = [Player(x, deepcopy(player_keymappings), self.boards[x]) for x in range(num_players)]

        self.control_string = ""
        self.control_box_width = 0
        self.control_box_height = 0
        self.get_controls_box()

    @property
    def score_display_width(self) -> int:
        """Determines how many horizontal grid spaces the score box takes up"""
        return max([len(x) for x in self.__str__().splitlines(False)])

    @property
    def score_display_height(self) -> int:
        """Determines how many vertical grid spaces the score box takes up"""
        return len(self.__str__().splitlines())

    @property
    def display_midpoint(self) -> tuple:
        """Determines the center point of the display string and returns it as an (x, y) pair"""
        x = sum((self.control_box_width, self.board_width_total, self.score_display_width)) // 2
        y = max((self.control_box_height, self.board_height_total, self.score_display_height)) // 2
        return x, y

    def reset(self):
        self.highscore = 0
        self.newgame()

    def newgame(self):
        self.next_piece = -1
        for b in self.boards:
            b.reset()
        self.gen_next_piece()

    def gen_next_piece(self):
        """Finds the next piece for play, if the game hasn't started yet, puts one in play.
        Then prepares the next piece"""
        tripped = False
        if self.next_piece >= 0:
            for b in self.boards:
                if b.read_for_piece:
                    b.new_piece(self.next_piece)
                    tripped = True
        else:
            tripped = True
            self.next_piece = random.choice(range(7))
            for b in self.boards:
                b.new_piece(self.next_piece)

        if tripped:
            self.next_piece = random.choice(range(7))

    # region Display Functions

    def get_controls_box(self):
        """Gets a box of text that contains the list of controls for the each player in the game.

        Also updates the control_box_width and control_box_height properties and the control_string property"""
        x, y = self.offset

        result = "Controls:\n\n"

        for i, p in enumerate(self.players):
            temp = control_arrows(p.keys)
            result += 'Player {}:\n'.format(i + 1)
            for line in temp.splitlines(True):
                result += '  ' + line
            result += '\n\n'

        self.control_string = boxed_text(result)

        split_control_string = self.control_string.splitlines(False)

        self.control_box_width = max([len(s) for s in split_control_string])
        self.control_box_height = len(split_control_string)

        x_off = x + self.control_box_width

        for i, b in enumerate(self.boards):
            b.offset = (x_off + self.board_width_adj * i, y)

    def get_score_box(self) -> str:
        """Gets the display box that contains the score data for each player"""
        data = "Highscore: {}\n".format(self.highscore)

        for p, b in enumerate(self.boards):
            data += "Player {}:\n".format(p)
            data += "    Lines: {}\n".format(b.lines)
            data += "    Score: {}\n".format(b.score)
            data += "    Level: {}\n".format(b.level)

        data += "Next Piece:\n"

        next_piece = boxed_text("    \n    \n    \n    "
                                if self.next_piece < 0 else str(int_to_block(self.next_piece, 0, 0))).splitlines(False)

        for next_piece_line in next_piece:
            data += " " + next_piece_line + " \n"

        return boxed_text(data[:-1])

    def __str__(self):

        display_list = [self.control_string]
        for b in self.boards:
            display_list.append(str(b))
        display_list.append(self.get_score_box())

        return hstack(display_list)

    def add_to_screen(self, screen):
        """Prints the tetris board out to the screen"""
        x, y = self.offset

        add_multiline_string(self.control_string, screen, x, y, False)

        for b in self.boards:
            b.add_to_screen(screen)

        add_multiline_string(self.get_score_box(), screen,
                             x + self.control_box_width + self.board_width_total, y, False)

    # endregion
