__author__ = 'John Ross'

import sys

unicode = "".join([chr(x) for x in range(sys.maxunicode)])

def expand(lst):
    if type(lst) is list:
        out = []

        for x in lst:
            out += expand(x)

        return [x for x in out if bool(x)]
    else:
        return [lst]