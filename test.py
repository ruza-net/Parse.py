__author__ = 'John Ross'

from parse import *
from utils import *

def main():
    w = word()
    lpar = liter("(")
    rpar = liter(")")

    rule = recurse()
    rule << name("call", name("name", w) + suppress(lpar) + name("args", count(0).more(w) ^ rule) + suppress(rpar))

    print(rule.parse("print(input(Enter a number))"))

if __name__ == "__main__":
    main()