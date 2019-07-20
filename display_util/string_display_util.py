import shutil
from colorama import Fore

import sys
import traceback
from enum import Enum

from .list_display_util import get_list_entry_str, ListTypes
from tetris.shared import KeyMappings


def clear(screen):
    """Clears the terminal screen as per
    https://stackoverflow.com/questions/517970/how-to-clear-the-interpreter-console"""
    screen.clear()
    screen.refresh()


def replace_tabs(string: str, tab_width: int = 4) -> str:
    """Takes an input string and a desired tab width and replaces each \\t in the string with ' '*tab_width."""

    return string.replace('\t', ' '*tab_width)


class AlignmentType(Enum):
    """A simple enum containing alignment types, left, center, right"""
    LEFT = 0
    CENTER = 1
    RIGHT = 2


def aligned_text(string: str, length: int, alignment: AlignmentType = AlignmentType.CENTER):
    """Returns a string that is aligned according to the parameters given"""
    diff = length - len(string)

    if diff < 0:
        raise AssertionError("Length of the string cannot be greater than the maximum length for alignment")

    if alignment == AlignmentType.LEFT:
        return string + ' ' * diff
    elif alignment == AlignmentType.CENTER:
        bit = ' ' * (diff // 2)
        return bit + string + bit + (' ' if diff % 2 == 1 else '')
    elif alignment == AlignmentType.RIGHT:
        return ' ' * diff + string


def hstack(strings: list, alignment: AlignmentType = AlignmentType.LEFT) -> str:
    """Stacks a series of multiline strings together horizontally"""
    string_list = [s.splitlines(False) for s in strings]
    widths = [max([len(s) for s in ss]) for ss in string_list]
    result = ""

    for i in range(max([len(s) for s in string_list])):
        for s in range(len(string_list)):
            sl = string_list[s]
            if i < len(sl):
                result += aligned_text(sl[i], widths[s], alignment)
            else:
                result += " " * widths[s]
        result += '\n'

    return result


def control_arrows(mappings: dict):
    """Creates a Controls layout display string for the given key mappings"""
    result = ""

    result_mappings = {'right': 'Not Assigned', 'left': 'Not Assigned', 'rotate': 'Not Assigned',
                       'drop': 'Not Assigned', 'soft drop': 'Not Assigned'}

    for k in mappings.values():
        m_l = list(mappings.values())
        index = m_l.index(k)
        mapping = mappings[list(mappings.keys())[index]]
        if mapping == KeyMappings.SHIFT_RIGHT:
            result_mappings['right'] = k
        elif mapping == KeyMappings.SHIFT_LEFT:
            result_mappings['left'] = k
        elif mapping == KeyMappings.ROTATE:
            result_mappings['rotate'] = k
        elif mapping == KeyMappings.DROP:
            result_mappings['drop'] = k
        elif mapping == KeyMappings.SOFT_DROP:
            result_mappings['soft drop'] = k

    result += '\u2192 : {} \n'.format(result_mappings['right'])
    result += '\u2190 : {} \n'.format(result_mappings['left'])
    result += '\u21BB : {} \n'.format(result_mappings['rotate'])
    result += '\u2193 : {} \n'.format(result_mappings['soft drop'])
    result += '\u21A1 : {} '.format(result_mappings['drop'])

    return result


def boxed_text(string: str, alignment: AlignmentType = AlignmentType.CENTER):
    lines = string.splitlines(False)
    width = max(len(x) for x in lines)
    height = len(lines)
    result = ""

    # Top line
    result += '\u2554'
    for k in range(width):
        result += '\u2550'
    result += '\u2557\n'

    # Body
    for h in range(height):
        result += '\u2551' + aligned_text(lines[h], width, alignment) + '\u2551\n'

    # Bottom line
    result += '\u255A'
    for k in range(width):
        result += '\u2550'
    result += '\u255D\n'

    return result


def centered_text(text: str, length: int = -1) -> str:
    """Returns a string that contains enough spaces to center the text in the context of the length given

    Defaults to centering the text in the width of the entire console

    text is stripped of leading and trailing whitespace before starting

    If length - len(text) is odd, then the extra space is appended to the end of the string

    If len(text) >= length, then text is returned

    If length is wider than the terminal width, then it is squeezed to fit

    Note: This does add spaces to the end of the string, not just the beginning, this allows for an accurate size in
    conjunction with other functions in this library"""

    t = text.strip()

    # If length is longer than the console width, then squeeze it to fit
    num_col = shutil.get_terminal_size((80, 20)).columns
    if length > num_col:
        length = num_col

    if len(t) >= length:
        return t

    space_tot = length - len(t)
    space_num = space_tot // 2

    space = " "*space_num

    if space_tot % 2 == 0:
        return space + t + space
    else:
        # Places the extra space at the end of the string
        return space + t + space + " "


def dashed_line(num: int, dash: str = '#') -> str:
    """Returns a string composed of num dashes"""

    temp = ""
    for i in range(num):
        temp += dash

    return temp


def print_dashes(num: int, dash: str = '#') -> str:
    """Prints out a single line of dashes with num chars
    If the num is larger than the console width, then a single console width is printed out instead"""

    # Gets the terminal width
    num_col = shutil.get_terminal_size((80, 20)).columns

    return dashed_line(num if num <= num_col else num_col, dash)


def hanging_indent(string: str, tab_width: int = 4) -> str:
    """Creates a hanging indent """

    # Gets the terminal width
    num_col = shutil.get_terminal_size((80, 20)).columns

    if len(string) <= num_col:
        # Returns a clone of the string, not the original
        return string[:]

    # Creates a tab string
    tab = " "*tab_width

    result = string[:num_col]
    remaining = string[num_col:]
    while True:
        if len(remaining) > num_col - tab_width:
            result += tab + remaining[:num_col - tab_width]
            remaining = remaining[num_col - tab_width:]
        else:
            result += tab + remaining
            break

    return result


def print_list(arr: list, format: str = "{}: {}", l_type: ListTypes = ListTypes.NUMERIC_ORDERED) -> str:
    """Prints a list to the screen in a neat fashion.

    format is a string used to determine layout of the element, default is '{}: {}' where the first is the index,
        and the second is the element."""

    result = ""
    for i, e in enumerate(arr):
        result += get_list_entry_str(e, i, format, l_type) + '\n'

    return result[:-1]


def print_info(string: str, begin: str = '') -> str:
    """Prints an info prompt to the console
    info prompts have '[INFO]' as a prefix and are printed in Yellow."""
    return begin + Fore.YELLOW + "[INFO] " + string + Fore.RESET


def print_warning(string: str, begin: str = '') -> str:
    """Prints an warning prompt to the console
    warning prompts have '[WARNING]' as a prefix and are printed in Red."""
    return begin + Fore.RED + "[WARNING] " + string + Fore.RESET


def print_error(string: str, begin: str = '') -> str:
    """Prints an error prompt to the console
    error prompts have '[ERROR]' as a prefix and are printed in Red."""
    return begin + Fore.RED + "[ERROR] " + string + Fore.RESET


def print_exception(begin: str = '') -> str:
    """Prints the current exception out to the console using the '[ERROR]' as a prefix and is printed in red.
    First line contains '[ERROR] Exception was thrown: <exception string>'
    Second line and on contains the full typical python traceback."""
    et, ev, tb = sys.exc_info()
    exc = begin + "Exception was thrown: {}\n".format(ev)
    for l in traceback.format_exception(et, ev, tb):
        exc += l
    return print_warning(exc)


def print_notification(string: str, begin: str = '') -> str:
    """Prints an notification prompt to the console
    notification prompts have '[NOTIFICATION]' as a prefix and are printed in Green."""
    return begin + Fore.GREEN + "[NOTIFICATION] " + string + Fore.RESET
