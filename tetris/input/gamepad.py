import pygame
from multiprocessing import Process, Queue
from enum import Enum
import time

pygame.init()
if not pygame.joystick.get_init():
    pygame.joystick.init()

pgj = pygame.joystick


def get_available() -> list:
    """Finds all available joysticks and returns them as a list"""
    result = []

    for i in range(pgj.get_count()):
        joy = pgj.Joystick(i)
        joy.init()
        result.append(joy)

    return result


def get_wrappers() -> list:
    """Finds all available joysticks and returns the GamePadWrappers as a list"""
    result = []
    for p in get_available():
        result.append(GamepadWrapper(p.get_id()))
    return result


def display_gamepad_info(pad: pgj.Joystick) -> str:
    return "Name: {}\nID: {}\nNumber of Axes: {}\nNumber of Balls: {}\n" \
           "Number of Buttons: {}\nNumber of Hats: {}".format(
            pad.get_name(),
            pad.get_id(),
            pad.get_numaxes(),
            pad.get_numballs(),
            pad.get_numbuttons(),
            pad.get_numhats()
            )


# region Tetris Wrapper

# region Events

# region Event Abstraction

# region Types

class GamePadEventType(Enum):
    DIRECTIONAL_PAD = 0
    BUTTON = 1


class HatPositionType(Enum):
    NOT_PRESSED = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


def position_to_type(value: int, vert: bool = True) -> HatPositionType:
    if value == 0:
        return HatPositionType.NOT_PRESSED
    elif vert:
        return HatPositionType.UP if value == 1 else HatPositionType.DOWN
    else:
        return HatPositionType.RIGHT if value == 1 else HatPositionType.LEFT

# endregion


class GamePadEventData:
    """Contains the data from a GamePadEvent"""

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class GamePadButtonEventData(GamePadEventData):
    """Contains the data from a button press or release"""

    def __init__(self, button_id: int, status: bool):
        self.button = button_id
        self.status = status

    def __eq__(self, other):
        if super().__eq__(other):
            return other.button == self.button and other.status == self.status
        else:
            return False

    def __str__(self) -> str:
        return "Button {}: {}".format(self.button, self.status)


class GamePadHatEventData(GamePadEventData):
    """Contains the data from a hat press or release"""

    def __init__(self, hat_id: int, hat_direction: HatPositionType, status: bool):
        self.hat = hat_id
        self.hat_button = hat_direction
        self.status = status

    def __eq__(self, other):
        if super().__eq__(other):
            return other.hat == self.hat and other.status == self.status and other.hat_button == self.hat_button

    def __str__(self) -> str:
        return "Hat {}: {} -> {}".format(self.hat, self.hat_button.name, self.status)


class GamePadEvent:
    """Contains an update about a joypad"""
    def __init__(self, event_type: GamePadEventType, joypad_id: int, data: GamePadEventData):
        self.event_type = event_type
        self.joypad = joypad_id
        self.data = data

    def __str__(self) -> str:
        return '{} from {} to state {}'.format(self.event_type.name, self.joypad, self.data)

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return other.event_type == self.event_type and other.joypad == self.joypad and other.data == self.data

# endregion


class PygameEventReader(Process):
    """Continuously polls the pygame event queue and pulls any gamepad data out of it.
    This should stop the event queue from freezing or causing problems"""

    stop_q = Queue(1)
    q = Queue()
    running = False

    def __init__(self, polling_interval: float = 0.05, hold_down_repeat: bool = True):
        super().__init__()
        self.interval = polling_interval
        self.repeat = hold_down_repeat
        self.previous_buttons = {}
        self.previous_hats = {}
        self.previous_values = {}
        for joy in range(pgj.get_count()):
            self.previous_values[joy] = (HatPositionType.NOT_PRESSED, HatPositionType.NOT_PRESSED)

    def join(self, **kwargs):
        self.stop_q.put(True)
        super().join(**kwargs)

    def run(self):
        if not self.running:
            self.running = True

        while self.stop_q.empty():
            start = time.time()
            changed_buttons = []
            changed_hats = []

            for event in pygame.event.get():

                if event.joy not in self.previous_buttons:
                    self.previous_buttons[event.joy] = {}
                if event.joy not in self.previous_hats:
                    self.previous_hats[event.joy] = {}

                if event.type == pygame.QUIT:
                    self.stop_q.put(True)

                elif event.type == pygame.JOYBUTTONDOWN:
                    self.q.put(GamePadEvent(GamePadEventType.BUTTON, event.joy,
                                            data=GamePadButtonEventData(event.button, True)))
                    self.previous_buttons[event.joy][event.button] = True
                    changed_buttons.append((event.joy, event.button))

                elif event.type == pygame.JOYBUTTONUP:
                    self.q.put(GamePadEvent(GamePadEventType.BUTTON, event.joy,
                                            data=GamePadButtonEventData(event.button, False)))
                    self.previous_buttons[event.joy][event.button] = False

                elif event.type == pygame.JOYHATMOTION:
                    if event.hat not in self.previous_hats[event.joy]:
                        self.previous_hats[event.joy][event.hat] = {}

                    t_h, t_v = event.value
                    tt_h, tt_v = position_to_type(t_h, False), position_to_type(t_v)
                    p_h, p_v = self.previous_values[event.joy]

                    # region Edge-detection

                    # Detects specific button presses
                    if tt_h != p_h:
                        self.q.put(GamePadEvent(GamePadEventType.DIRECTIONAL_PAD, event.joy,
                                                data=GamePadHatEventData(event.hat, p_h, False)))
                        self.previous_hats[event.joy][event.hat][p_h] = False

                        p_h = tt_h
                        self.q.put(GamePadEvent(GamePadEventType.DIRECTIONAL_PAD, event.joy,
                                                data=GamePadHatEventData(event.hat,
                                                                         p_h, True)))
                        self.previous_hats[event.joy][event.hat][p_h] = True
                        changed_hats.append((event.joy, event.hat, p_h))

                    if tt_v != p_v:
                        self.q.put(GamePadEvent(GamePadEventType.DIRECTIONAL_PAD, event.joy,
                                                data=GamePadHatEventData(event.hat, p_v, False)))
                        self.previous_hats[event.joy][event.hat][p_v] = False

                        p_v = tt_v
                        self.q.put(GamePadEvent(GamePadEventType.DIRECTIONAL_PAD, event.joy,
                                                data=GamePadHatEventData(event.hat,
                                                                         p_v, True)))
                        self.previous_hats[event.joy][event.hat][p_v] = True
                        changed_hats.append((event.joy, event.hat, p_v))

                    # Saves the current state as the previous
                    self.previous_values[event.joy] = (p_h, p_v)

                    # endregion

            # # region Button holding detection
            #
            # if self.repeat:
            #     for j in self.previous_buttons:
            #         for b in self.previous_buttons[j]:
            #             if self.previous_buttons[j][b] and (j, b) not in changed_buttons:
            #                 self.q.put(GamePadEvent(GamePadEventType.BUTTON, j, data=GamePadButtonEventData(b, True)))
            #
            #     for j in self.previous_hats:
            #         for h in self.previous_hats[j]:
            #             for d in self.previous_hats[j][h]:
            #                 if self.previous_hats[j][h][d] and (j, h, d) not in changed_hats:
            #                     self.q.put(GamePadEvent(GamePadEventType.DIRECTIONAL_PAD, j,
            #                                             data=GamePadHatEventData(h, d, True)))
            #
            # # endregion

            diff = time.time() - start
            if diff < self.interval:
                time.sleep(self.interval - diff)

# endregion


class GamepadWrapper:
    """Wraps the various kinds of joysticks out there, right now it supports PS4 and XBOX"""

    event_reader = None

    def __init__(self, mid: int = 0, polling_interval: float = 0):
        self.joy = pgj.Joystick(mid)
        self.joy.init()
        self.interval = polling_interval

        if self.event_reader is None or not PygameEventReader.running:
            if self.event_reader is not None:
                self.event_reader.start()
            else:
                self.event_reader = PygameEventReader(self.interval)
                self.event_reader.start()

    def __del__(self):
        self.joy.quit()

# endregion
