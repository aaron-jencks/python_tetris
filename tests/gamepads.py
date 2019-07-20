import tetris.input.gamepad as gp
import pygame


pygame.init()


if __name__ == "__main__":
    sticks = []
    qs = gp.PygameEventReader.q

    for stick in gp.get_available():
        print(gp.display_gamepad_info(stick) + '\n')
        sticks.append(gp.GamepadWrapper(stick.get_id()))

    print('Listening...')
    while True:
        event = qs.get()
        print(event)
