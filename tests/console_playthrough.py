from tetris.classes import Tetris


class Game(Tetris):
    def __init__(self, num_players: int = 1, board_width: int = 10, board_height: int = 20, scale: int = 1):
        super().__init__(0, 0, num_players, board_width, board_height, scale)
        self.is_stopping = False
        self.reset()

    @property
    def center_pos(self) -> tuple:
        """Returns the coordinates of the center of the playing boards"""
        x, y = self.offset
        return x + self.control_box_width + (len(self.boards) * self.board_width) // 2, y + self.board_height // 2

    def refresh_screen(self):
        """Paints the window to the console"""
        print(self)

    def start(self):
        """Starts the game"""
        self.newgame()
        self.refresh_screen()
        self.__event_loop()

    def __event_loop(self):
        """Loops and collects user-input, using it as necessary and calling the corresponding methods"""

        while not self.is_stopping:
            self.refresh_screen()
            key = ord(input()[0])

            if key >= 0:
                # Check if the key was a valid move
                ch_mod = chr(key)
                for p in self.players:
                    if key in p.keys:
                        # Runs the move if it was found
                        p.mappings[ch_mod]()
                        break

                for b in self.boards:
                    b.update()

            else:
                for b in self.boards:
                    b.update()
                continue


if __name__ == "__main__":
    g = Game(4, scale=2)
    g.start()
