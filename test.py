__author__ = 'John Ross'

#import json
from parse import *
from utils import *

def main():
    setIgnored(" \n\t")

    id = combine(word(ascii + "_") + optional(word(ascii_nums + "_")))

    IF = key("if")
    END = key("end")
    AND = key("and")
    OR = key("or")

    eqeq = liter("==")
    colon = liter(":")
    lpar = liter("(")
    rpar = liter(")")

    string = name("string", combine(suppress(liter('"')) + skipTo(liter('"'), esc="\\", suppress=True)))

    funcal = recurse()
    funcal << name("call", name("name", id) + suppress(lpar) + name("args", separated(funcal | string)) + suppress(rpar))

    value = string | funcal | name("id", id)

    cond = recurse()
    cond << name("condition", name("equals", value + suppress(eqeq) + value) + optional(suppress(AND | OR) + cond))

    _if = name("if", suppress(IF) + cond + suppress(colon) + funcal + suppress(END))

    code = _if | funcal

    s1 = """
            if name == "John Ross":
                print("Hello world!")
            end

    """

    s2 = """
            print(input("Enter your name: "), "is", input("Enter your age: "), "years old.")
    """

    ast = code.parse(s2)[0]

if __name__ == "__main__":
    main()
