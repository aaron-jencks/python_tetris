from .string_display_util import print_error, print_dashes, hanging_indent, centered_text, replace_tabs, clear, \
    boxed_text
from .list_display_util import ListTypes, get_list_entry_str

from colorama import Fore
import curses

from copy import deepcopy
from multiprocessing import Queue


def add_multiline_string(string: str, screen, x_pos: int = 0, y_pos: int = 0, refresh: bool = True):
    """Adds a multiline string to the given screen"""

    for i, l in enumerate(string.splitlines(False)):
        screen.addstr(y_pos + i, x_pos, l)

    if refresh:
        screen.refresh()


def get_constrained_input(prompt: str, constraint, screen, x_pos: int = 0, y_pos: int = 0) -> str:
    """Prompts the user for input, continues to prompt the user for input until the lambda expression passed in for
        constraint returns True."""

    key = ''

    add_multiline_string(boxed_text(Fore.GREEN + prompt + Fore.RESET), screen, x_pos, y_pos)

    while True:
        try:
            key = screen.getkey()
            break
        except curses.error:
            continue

    while not constraint(key):
        add_multiline_string(boxed_text(print_error("Invalid Response!")), screen, x_pos, y_pos)

        curses.napms(1000)
        add_multiline_string(boxed_text(Fore.GREEN + prompt + Fore.RESET), screen, x_pos, y_pos)

        while True:
            try:
                key = screen.getkey()
                break
            except curses.error:
                continue

    return key


def console_box_menu(options: dict, screen, list_format: str = "{}: {}", title: str = "", centered_title: bool = True,
                     tab_width: int = 4, x_pos: int = 0, y_pos: int = 0):
    """Creates a console style menu with the given options as choices to choose from
    Returns a key that was chosen from the options dict.
    Keys must be either a str or have a __str__() defined

    Arguments:

    options: a dict containing keys that are choices for users, and values that are descriptions for each key,
        the chosen key will be returned.

    list_format: uses similar syntax to str.format(), the default is \"{}: {}\" where the first {} is the key, and the
        second {} is the value.

    title: the title string displayed at the top of the menu.

    centered_title: True if the title string should be centered in the console.

    dash: character or string used as the duplicated dash sequence for the bars at the top and bottom of the menu.

    tab_width: width, in number of spaces, considered to be a single tab."""

    # Determines the longest string entry of the set of options
    entries = [list_format.format(k, options[k]) for k in options]
    max_length = max([len(x) for x in entries])
    if len(title) > max_length:
        max_length = len(title)

    # Creates the menu
    prompt = ''
    prompt += (centered_text(title, max_length) if centered_title else title) + "\n"
    prompt += "Options: \n"
    for e in entries:
        prompt += hanging_indent(e, tab_width) + '\n'

    add_multiline_string(prompt, screen, x_pos, y_pos)

    # Prompts the user for input and ensures validity
    valid = [str(k) for k in options.keys()]

    choice = get_constrained_input("Choice? ", lambda x: x in valid, screen, x_pos, y_pos)

    # Finds the said choice and returns it
    index = valid.index(choice)
    return list(options.keys())[index]


def console_gamepad_box_menu(options: dict, screen, event_q: Queue, list_format: str = "{}: {}", title: str = "",
                             centered_title: bool = True, tab_width: int = 4,
                             x_pos: int = 0, y_pos: int = 0):
    """Creates a console style menu with the given options as choices to choose from
    Returns a key that was chosen from the options dict.
    Keys must be either a str or have a __str__() defined

    Arguments:

    options: a dict containing keys that are choices for users, and values that are descriptions for each key,
        the chosen key will be returned.

    list_format: uses similar syntax to str.format(), the default is \"{}: {}\" where the first {} is the key, and the
        second {} is the value.

    title: the title string displayed at the top of the menu.

    centered_title: True if the title string should be centered in the console.

    dash: character or string used as the duplicated dash sequence for the bars at the top and bottom of the menu.

    tab_width: width, in number of spaces, considered to be a single tab."""

    selected_index = 0
    done = False

    # Determines the longest string entry of the set of options
    entries = [list_format.format(k, options[k]) for k in options]
    max_length = max([len(x) for x in entries])
    if len(title) > max_length:
        max_length = len(title)

    # Prompts the user for input and ensures validity
    valid = [str(k) for k in options.keys()]

    while not done:

        # Creates the menu
        prompt = ''
        prompt += (centered_text(title, max_length) if centered_title else title) + "\n"
        prompt += "Options: \n"
        for i, e in enumerate(entries):
            if i == selected_index:
                prompt += '->'
            prompt += hanging_indent(e, tab_width) + '\n'

        add_multiline_string(boxed_text(prompt), screen, x_pos, y_pos)
        screen.refresh()

        choice = event_q.get(block=True)
        # TODO Process gamepad events

        # Finds the said choice and returns it
        index = valid.index(choice)
        return list(options.keys())[index]
