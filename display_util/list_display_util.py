from enum import Enum


class ListTypes(Enum):
    NUMERIC_ORDERED = 0
    ALPHA_ORDERED = 1
    UNORDERED = 2


def get_character_bullet(index: int) -> str:
    """Takes an index and converts it to a string containing a-z, ie.

    0 -> 'a'
    1 -> 'b'
    .
    .
    .
    27 -> 'aa'
    28 -> 'ab'

    """

    result = chr(ord('a') + index % 26)  # Should be 0-25

    if index > 25:
        current = index // 26

        while current > 0:
            result = chr(ord('a') + (current - 1) % 25) + result
            current = current // 26

    return result


def get_list_entry_str(entry, index: int = -1,
                       entry_format: str = "{}: {}", l_type: ListTypes = ListTypes.NUMERIC_ORDERED) -> str:
    """Returns a formatted list entry item according to the items given."""

    if l_type == ListTypes.NUMERIC_ORDERED:
        return entry_format.format(index, entry)
    elif l_type == ListTypes.ALPHA_ORDERED:
        return entry_format.format(get_character_bullet(index), entry)
    else:
        return entry_format.format('•', entry)
