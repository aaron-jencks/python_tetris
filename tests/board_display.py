from tetris.classes import Board


if __name__ == "__main__":
    b = Board(0, 0, lambda: True, scale=2)
    print(b)
