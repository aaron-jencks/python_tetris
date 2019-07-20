from tetris.classes import Tetris
from display_util.string_display_util import hstack


if __name__ == "__main__":
    t = Tetris(0, 0, 4, scale=2)
    print(t)
    for b in t.boards:
        print(b.offset)
