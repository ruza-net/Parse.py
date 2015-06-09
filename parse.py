__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "1.0.0"

from utils import *
import sys


_ignored = " "
_recursed = {}
_keywords = []

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
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            return And(self, key(other))

        return And(self, other)

    def __or__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            return Or(self, key(other))

        return Or(self, other)

    def __xor__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            return Xor(key(other), self)

        return Xor(self, other)

    def __radd__(self, other):
        o = key(other)
        return And(o, self)

    def __ror__(self, other):
        o = key(other)
        return Or(o, self)

    def __rxor__(self, other):
        o = key(other)
        return Xor(o, self)

    def __invert__(self):
        return Not(self)

    def __neg__(self):
        return Not(self)


# EOF

class doc_end(element):
    def __init__(self):
        super(doc_end, self).__init__("")

    def parse(self, string):
        while len(string) > 0 and string[0] in _ignored:
            string = string[1:]

        assert len(string) == 0, "Expecting an EOF in `%s`!" % string

        return "", ""

    def __str__(self):
        return " <EOF>"


# Suppress an element

class suppress(element):
    def __init__(self, value):
        super(suppress, self).__init__(str(value))

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        return "", string

    def __str__(self):
        return "(?: " + str(self.value) + " )"


# Skip to element

class skipTo(element):
    def __init__(self, value, **kwargs):
        super(skipTo, self).__init__(str(value))

        self.esc = kwargs.get("esc", None)
        self.suppress = kwargs.get("suppress", False)

        self.value = value

    def parse(self, string):
        piece = ""
        i = 0
        while True:
            try:
                assert piece[-1] != self.esc

                a, string = self.value.parse(string)

                if self.suppress:
                    return piece.replace(self.esc, ""), string
                else:
                    return [piece.replace(self.esc, ""), a], string
            except:
                assert len(string) > 0, "Can't skip to `%s`!" % str(self.value)

                piece += string[0]
                string = string[1:]


# List separated by elements

class separated(element):
    def __init__(self, value, **kwargs):
        super(separated, self).__init__("")

        self.sep = kwargs.get("sep", liter(","))
        self.suppress = kwargs.get("suppress", False)

        self.min = kwargs.get("min", 0)
        self.max = kwargs.get("max", -1)

        self.value = value

    def parse(self, string):
        out = []

        while True:
            a, string = self.value.parse(string)
            out.append(a)

            try:
                string = self.sep.parse(string)[1]
            except:
                break

        assert len(out) > self.min, "Minimal length %i not humbled!" % self.min
        assert len(out) < self.max or self.max == -1, "Maximal length %i humbled!" % self.max

        return expand(out), string


# Classic elements

class word(element):
    def __init__(self, chars=ascii):
        super(word, self).__init__("")

        self.chars = chars

    def parse(self, string):
        bak = string
        v, string = self.valid(string)

        assert len(v) > 0, "Invalid characters used in `%s`!" % string

        if v in _keywords:
            return "", bak
        else:
            return v, string

    def valid(self, string):
        i = 0
        while len(string) > 0 and string[0] in _ignored:
            string = string[1:]

        validWord = ""
        for i, x in enumerate(list(string)):
            if x not in self.chars:
                break
            else:
                validWord += x

        return validWord, string[len(validWord):]

    def __str__(self):
        return "[" + self.chars + "]"

class liter(element):
    def __init__(self, lit):
        super(liter, self).__init__(lit)

        self.lit = lit

    def parse(self, string):
        while len(string) > 0 and string[0] in _ignored:
            string = string[1:]

        assert string[:len(self.lit)] == self.lit, "Invalid literal `%s`, expecting `%s`!" % (string[:len(self.lit)], self.lit)

        return self.lit, string[len(self.lit):]

    def __str__(self):
        return "'" + self.lit + "'"

class key(element):
    def __init__(self, k):
        super(key, self).__init__(str(k))

        _keywords.append(k)
        self.k = liter(k)

    def parse(self, string):
        a, string = self.k.parse(string)

        assert len(string) == 0 or string[0] in _ignored, "`key` object requires whitespaces around `%s`!" % string

        return a, string

    def __str__(self):
        return str(self.k)


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
        return "?( " + str(self.value) + " )"

class group(element):
    def __init__(self, value):
        super(group, self).__init__(str(value))
        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)
        return tuple(expand(a)), string

    def __str__(self):
        return "( " + str(self.value) + " )"

class combine(element):
    def __init__(self, value):
        super(combine, self).__init__(str(value))
        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)
        return "".join(expand(a)), string

    def __str__(self):
        return ">" + str(self.value) + "<"


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
        return "{" + str(self.name) + ": " + str(self.value) + " }"


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

class Not(element):
    def __init__(self, value):
        super(Not, self).__init__(str(value))

        self.value = value

    def parse(self, string):
        try:
            self.value.parse(string)
        except:
            return "", string

        raise SyntaxError("Not expecting `%s` in `%s`!" % (str(self.value), string))


# TODO: !DANGER - COMPLICATED (AND RECURSIVE) ELEMENTS!

class recurse(element):
    def __init__(self):
        super(recurse, self).__init__("")

        self.id = len(_recursed)
        _recursed[self.id] = None

    def __lshift__(self, value):
        _recursed[self.id] = value

    def parse(self, string):
        try:
            #return
            a, string = _recursed[self.id].parse(string)
        except RuntimeError:
            raise RuntimeError("Recurse element execution failed!")
        except:
            raise

        return a, string

    def __str__(self):
        return "<parse.recurse::" + str(self.id) + ">"


DOC_END = doc_end()
