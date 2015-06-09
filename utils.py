__author__ = 'John Ross'

import sys
import string

unicode = "".join([chr(x) for x in range(sys.maxunicode)])
ascii = string.ascii_lowercase + string.ascii_uppercase
nums = "".join(str(x) for x in range(10))
ascii_nums = ascii + nums

def expand(lst):
    if type(lst) is list:
        out = []

        for x in lst:
            out += expand(x)

        out = [x for x in out if bool(x)]

        return out
    else:
        return [lst]