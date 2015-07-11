__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "0.5.0"

import sys
import string
import re

unicode = "".join([chr(x) for x in range(sys.maxunicode)])
ascii = string.ascii_lowercase + string.ascii_uppercase
nums = "".join(str(x) for x in range(10))
ascii_nums = ascii + nums


def expand(lst):
    """
    Will expand list to linear view. For example:
        - ["Hello", ["world", "!"]] -> ["Hello", "world", "!"]
        - ["Hello", ""] -> "Hello"      # Empty elements are cut off, if length is 1, return first element.
        - ["Hello", ("world", "!")] -> ["Hello", ("world", "!")]
    """

    if type(lst) is list:
        out = []

        for x in lst:
            out += expand(x)

        out = [x for x in out if bool(x)]

        return out
    else:
        return [lst]


def Minimize(a):
    if type(a) is list:
        if len(a) == 1:
            return a[0]
        else:
            return tuple(a)

def escapes(string):
    string = re.sub(r'\\(?=.)', r'\\', string)
    return string