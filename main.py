import curses
import time
from queue import Empty

from tetris.classes import Tetris
from display_util.string_display_util import boxed_text
from display_util.menu import add_multiline_string
from tetris.input.gamepad import PygameEventReader, GamePadEventType
import tetris.input.gamepad as gp


# TODO Create start and pause menus

# TODO Fix control display panel
# TODO Test the new piece_control fixes for button-repeating when a button is held
# TODO Get Gamepad working in the main game (Port piece_control.py over to main.py)

# TODO Wire up the controls and collision detection
# TODO Configure scoring

# Reference: https://www.colinfahey.com/tetris/tetris.html

class Game(Tetris):
    def __init__(self, screen, num_players: int = 1, board_width: int = 10, board_height: int = 20, scale: int = 1):
        super().__init__(0, 0, num_players, board_width, board_height, scale)
        self.screen = screen
        self.is_stopping = False
        self.reset()

        self.event_q = PygameEventReader.q

        self.sticks = gp.get_wrappers()

    @property
    def center_pos(self) -> tuple:
        """Returns the coordinates of the center of the playing boards"""
        x, y = self.offset
        return x + self.control_box_width + (len(self.boards) * self.board_width) // 2, y + self.board_height // 2

    def refresh_screen(self):
        """Paints the window to the console"""
        self.add_to_screen(self.screen)
        self.screen.refresh()

    def __show_countdown(self):
        """Counts down from 10 on each player's board while showing what the starting piece will be."""
        for i in range(10, 0, -1):
            self.refresh_screen()
            for b in self.boards:
                x, y = b.offset
                x += self.board_width_adj // 2
                y += self.board_height_total // 2
                self.screen.addstr(y, x, "{}".format(i))
            self.screen.refresh()
            time.sleep(1)

    def start(self):
        """Starts the game"""
        self.newgame()
        self.refresh_screen()
        self.__show_countdown()
        self.__event_loop()

    def main_menu(self):
        """Displays the main menu for the game"""
        pass

    def pause(self):
        """Pauses the game"""

        # Creates and displays the pause menu
        pause_string = boxed_text("Paused!\nPress any key to continue...")
        x, y = self.display_midpoint
        add_multiline_string(pause_string, self.screen, x - 14, y - 2)
        self.screen.refresh()

        # Spins until a player presses ESCAPE ('^[') again
        while True:
            key = self.event_q.get()

            if key.event_type == GamePadEventType.BUTTON:
                if key.data.button == 9 and not key.data.status:
                    self.refresh_screen()
                    break
                else:
                    continue
            else:
                continue

    def __event_loop(self):
        """Loops and collects user-input, using it as necessary and calling the corresponding methods"""

        while not self.is_stopping:
            self.refresh_screen()

            try:
                event = self.event_q.get_nowait()

                # Check if the button corresponds to a player
                for p in self.players:
                    if event.joypad in p:
                        if event.data in p:
                            index = list(p.keys.values()).index(event.data)
                            p.get_function(list(p.keys.keys())[index])()

                if event.event_type == GamePadEventType.BUTTON:
                    # Check if the key was a menu key
                    if event.data.button == 9 and not event.data.status:
                        self.pause()
                        continue
                    else:
                        self.screen.addstr(0, 0, str(event))
                        self.screen.refresh()
                        time.sleep(1)

            except Empty:
                for b in self.boards:
                    b.update()
                continue


def main():

    # region Initializes the curses screen

    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    # Turns off blocking until user-input
    stdscr.nodelay(True)

    # endregion

    stdscr.clear()

    try:

        t = Game(stdscr, 1, scale=2)

        t.start()

        stdscr.refresh()
        stdscr.getkey()

    finally:

        # region Terminates the curses screen

        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

        # endregion


if __name__ == '__main__':
    main()
