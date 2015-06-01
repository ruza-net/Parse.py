__author__ = 'John Ross'

from parse import *
from utils import *

def main():
    setIgnored(" \n\t")

    w = word()

    eq = liter("=")
    colon = liter(":")

    _if = key("if")
    _end = key("end")
    _and = key("and")
    _or = key("or")

    condition = recurse()
    condition << (w + eq + w + optional((_and | _or) + condition))

    rule = recurse()
    rule << name("if", suppress(_if) + name("cond", condition) + suppress(colon) + name("body", rule | optional(count(1).more(w))) + suppress(_end))

    t1 = """
            if hello = world:
                if myName = John:
                end
            end
        """

    t2 = """
            if name = Paul:
            end
        """

    t3 = """
            if hello = world:
                hi
            end
        """

<<<<<<< HEAD
    print(rule.parse(t1)[0])
    print(rule.parse(t2)[0])
    print(rule.parse(t3)[0])
=======
    print(rule.parse("print(input(Enter a number))")[0)
>>>>>>> origin/master

if __name__ == "__main__":
    main()
