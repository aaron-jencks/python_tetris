import curses
import random
import time
import pygame
from queue import Empty

import tetris.input.gamepad as gp
from tetris.shared import int_to_block, KeyMappings
from tetris.input.gamepad import GamePadEventType, HatPositionType, display_gamepad_info, \
    GamePadButtonEventData, GamePadHatEventData, PygameEventReader
from tetris.classes import Player, Board


pygame.init()


delay = 0.5


def gen_new_piece(b: Board):
    b.new_piece(random.randint(0, 6))


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

    q = gp.PygameEventReader.q
    sticks = gp.get_wrappers()
    for s in sticks:
        display_gamepad_info(s.joy)

    # region Player setup

    player_keymappings = {KeyMappings.SHIFT_LEFT: GamePadHatEventData(0, HatPositionType.LEFT, True),
                          KeyMappings.SOFT_DROP: GamePadHatEventData(0, HatPositionType.DOWN, False),
                          KeyMappings.SHIFT_RIGHT: GamePadHatEventData(0, HatPositionType.RIGHT, True),
                          KeyMappings.ROTATE: GamePadButtonEventData(0, False),
                          KeyMappings.DROP: GamePadButtonEventData(3, False)}

    b1 = None
    b1 = Board(0, 0, lambda: gen_new_piece(b1))
    p1 = Player(0, player_keymappings, b1)
    b1.reset()

    # endregion

    # p = int_to_block(random.randint(0, 6), 10, 10)

    try:

        while True:
            start = time.time()
            stdscr.clear()
            b1.add_to_screen(stdscr)
            stdscr.refresh()
            broken = False

            while time.time() - start < delay:

                b1.add_to_screen(stdscr)
                stdscr.refresh()

                try:
                    event = q.get_nowait()

                    if event.data in p1:
                        if event.event_type == GamePadEventType.BUTTON:
                            if not event.data.status:
                                if event.data.button == 3:
                                    b1.drop()
                                elif event.data.button == 0:
                                    b1.rotate()
                        elif event.event_type == GamePadEventType.DIRECTIONAL_PAD:
                            if not event.data.status:
                                if event.data.hat_button == HatPositionType.RIGHT:
                                    b1.right()
                                elif event.data.hat_button == HatPositionType.LEFT:
                                    b1.left()

                    if event.event_type == GamePadEventType.BUTTON:
                        if event.data.button == 9:
                            broken = True
                            break

                except Empty:
                    pass

            if broken:
                break

            b1.update()

    finally:

        # Stops the joypad interface reader

        PygameEventReader.stop_q.put(True)

        # region Terminates the curses screen

        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

        # endregion


if __name__ == "__main__":
    main()
