__author__ = 'John Ross'

from utils import *
import sys


_ignored = " "
_recursed = {}

def setIgnored(val):
    global _ignored

    _ignored = val


# Default primitive element

class element:
    def __init__(self, string):
        self.string = string

    def length(self):
        return len(str(self.string))

    def __add__(self, other):
        if not issubclass(type(other), element):
            raise TypeError("Can't combine element and %s!" % type(other))

        return And(self, other)

    def __or__(self, other):
        if not issubclass(type(other), element):
            raise TypeError("Can't combine element and %s!" % type(other))

        return Or(self, other)

    def __xor__(self, other):
        if not issubclass(type(other), element):
            raise TypeError("Can't combine element and %s!" % type(other))

        return Xor(self, other)


# EOF

class doc_end(element):
    def __init__(self):
        super(doc_end, self).__init__("")

    def parse(self, string):
        assert len(string) == 0, "Expecting an EOF in `%s`!" % string

        return "", ""


# Suppress an element

class suppress(element):
    def __init__(self, value):
        super(suppress, self).__init__(str(value))

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        return "", string

    def __str__(self):
        return "(?:'" + str(self.value) + "')"

# Classic elements

class word(element):
    def __init__(self, chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        super(word, self).__init__("")

        self.chars = chars

    def parse(self, string):
        v, string = self.valid(string)

        assert len(v) > 0, "Invalid characters used in `%s`!" % string

        return v, string

    def valid(self, string):
        i = 0
        while string[0] in _ignored:
            string = string[1:]

        validWord = ""
        for i, x in enumerate(list(string)):
            if x not in self.chars:
                break
            else:
                validWord += x

        return validWord, string[len(validWord):]

class liter(element):
    def __init__(self, lit):
        super(liter, self).__init__(lit)

        self.lit = lit

    def parse(self, string):
        while string[0] in _ignored:
            string = string[1:]

        assert string[:len(self.lit)] == self.lit, "Invalid literal `%s`!" % string[:len(self.lit)]

        return self.lit, string[len(self.lit):]

    def __str__(self):
        return self.lit

class key(element):
    def __init__(self, k):
        super(key, self).__init__(str(k))

        self.k = liter(k)

    def parse(self, string):
        a, string = self.k.parse(string)


        c = 0
        while string[0] in _ignored:
            string = string[1:]
            c += 1

        if c == 0:
            raise SyntaxError("`key` object requires whitespaces around `%s`!" % string)

        return a, string


# Additional control structures

class optional(element):
    def __init__(self, value):
        super(optional, self).__init__(str(value))

        self.value = value

    def parse(self, string):
        a = ""
        try:
            a, string = self.value.parse(string)
        except:
            pass

        return expand(a), string

    def __str__(self):
        return "?" + str(self.value)

class group(element):
    def __init__(self, value):
        super(group, self).__init__(str(value))

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        return tuple(expand(a)), string

    def __str__(self):
        return "(" + str(self.value) + ")"


# Counter

class count(element):
    def __init__(self, cnt):
        super(count, self).__init__("")

        self.count = cnt

    def match(self, value):
        code = value
        for i in range(self.count-1):
            code += value
        return code

    def upTo(self, max, value):
        code = value

        for i in range(self.count-1, max):
            if i > 0:
                c1 = value
                for x in range(i):
                    c1 += value

                code = Xor(code, c1)

        return code

    def less(self, value):
        tmp = count(1)

        return tmp.upTo(self.count, value)

    def more(self, value):
        return self.upTo(80, value)


# Named output

class name(element):
    def __init__(self, nam, value):
        super(name, self).__init__(nam)

        self.name = nam
        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        return {self.name: a}, string

    def __str__(self):
        return "{" + str(self.name) + ": " + str(self.value) + "}"


# Operator classes

class And(element):
    def __init__(self, first, second):
        super(And, self).__init__(str(first) + str(second))

        self.first = first
        self.second = second

    def parse(self, string):
        a, string = self.first.parse(string)
        b, string = self.second.parse(string)

        return expand([a, b]), string

    def __str__(self):
        return str(self.first) + " + " + str(self.second)

class Or(element):
    def __init__(self, first, second):
        super(Or, self).__init__(str(first) + str(second))

        self.first = first
        self.second = second

    def parse(self, string):
        a = ""
        try:
            a, string = self.first.parse(string)
        except:
            a, string = self.second.parse(string)

        return expand(a), string

    def __str__(self):
        return str(self.first) + " | " + str(self.second)

class Xor(element):
    def __init__(self, first, second):
        super(Xor, self).__init__(str(first) + str(second))

        self.first = first
        self.second = second

    def parse(self, string):
        bak = string

        a = ""
        b = ""
        try:
            a, string = self.first.parse(string)
            try:
                b, bak = self.second.parse(bak)
            except:
                pass
        except:
            b, string = self.second.parse(string)

        if len(bak) > len(string):
            return expand(a), string
        else:
            return expand(b), bak

    def __str__(self):
        return str(self.first) + " ^ " + str(self.second)


# TODO: !DANGER - COMPLICATED (AND RECURSIVE) ELEMENTS!

class recurse(element):
    def __init__(self):
        super(recurse, self).__init__("")

        self.id = len(_recursed)
        _recursed[self.id] = None

    def __lshift__(self, value):
        _recursed[self.id] = value

    def parse(self, string):
        a, string = _recursed[self.id].parse(string)

        return a, string


DOC_END = doc_end()