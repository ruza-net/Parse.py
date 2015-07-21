__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "1.0.5"

from utils import *
import sys
import re


_ignored = " "

_recursed = {}

_keywords = []
_literals = []

_ops = {}


def _addOp(op, att):
    if type(op) in [And, Or, Xor]:
        _addOp(op.first, att)
        _addOp(op.second, att)
    else:
        _ops[str(op)] = att


def setIgnored(val):
    global _ignored

    _ignored = val


class opAssoc:
    left = 1
    right = 2


class opType:
    unary = 1
    binary = 2
    ternary = 3


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
            other = liter(other)

        return And(self, other)

    def __or__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            other = liter(other)

        return Or(self, other)

    def __xor__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            other = liter(other)

        return Xor(self, other)

    def __radd__(self, other):
        o = key(other)
        return And(o, self)

    def __ror__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            other = liter(other)

        return Or(other, self)

    def __rxor__(self, other):
        if not issubclass(type(other), element) and type(other) is not str:
            raise TypeError("Can't combine element and %s!" % type(other))

        if type(other) is str:
            other = liter(other)

        return Xor(other, self)

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

        if not issubclass(type(value), element):
            value = liter(value)

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

        self.esc = kwargs.get("esc", "\\")
        self.cut = kwargs.get("cut", True)
        self.suppress = kwargs.get("suppress", False)

        if not issubclass(type(value), element):
            value = liter(value)

        self.value = value

    def parse(self, string):
        piece = ""
        i = 0
        while True:
            try:
                assert piece[-1] != self.esc

                if self.cut:
                    a, string = self.value.parse(string)
                else:
                    a = self.value.parse(string)

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

        stop = kwargs.get("stop", None)

        self.sep = kwargs.get("sep", liter(","))

        self.cut = kwargs.get("cut", True)
        self.suppress = kwargs.get("suppress", True)

        self.min = kwargs.get("min", -1)
        self.max = kwargs.get("max", -1)

        if stop:
            self.stop = stop
        else:
            self.stop = None

        if not issubclass(type(value), element):
            value = liter(value)
        if type(self.sep) is str:
            self.sep = liter(self.sep)

        self.value = value

        if type(self.sep) is str:
            self.sep = liter(self.sep)
        if type(self.stop) is str:
            self.stop = liter(self.stop)
        if type(self.value) is str:
            self.value = liter(self.value)

    def parse(self, string):
        out = []

        sep = True
        while True:
            try:
                assert sep

                a, string = self.value.parse(string)
                out.append(a)

                sep = False

                if self.stop:
                    try:
                        if self.cut:
                            string = self.stop.parse(string)[1]
                        else:
                            self.stop.parse(string)

                        break
                    except:
                        pass

                s, string = self.sep.parse(string)

                sep = True

                if not self.suppress:
                    out.append(s)

            except:
                break

        assert len(out) >= self.min, "Minimal length %i not humbled!" % self.min
        assert len(out) <= self.max or self.max == -1, "Maximal length %i humbled!" % self.max

        return expand(out), string

    def __str__(self):
        return "[ %s%s ... ]" % (str(self.value), str(self.sep))


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
        while len(string) > 0 and string[0] in _ignored and string[0] not in self.chars:
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


class regex(element):
    def __init__(self, exp):
        super(regex, self).__init__(exp)

        self.exp = escapes(exp)

    def parse(self, string):
        a = None
        while len(string) > 0 and string[0] in _ignored:
            a = re.match(self.exp, string)
            if a:
                break

            string = string[1:]

        if not a:
            a = re.match(self.exp, string)

            if not a:
                raise SyntaxError("Regex evaluation fault!")

        #assert a.group(0) not in _literals and a.group(0) not in _keywords

        return [a.group(0)], string[len(a.group(0)):]

    def __str__(self):
        return repr(str(self.exp))[1:-1]


class liter(element):
    def __init__(self, lit):
        super(liter, self).__init__(lit)

        if lit not in _keywords:
            _literals.append(lit)

        self.lit = lit

    def parse(self, string):
        while len(string) > 0 and string[0] in _ignored and string[:len(self.lit)] != self.lit:
            try:
                assert string[:len(self.lit)] == self.lit, "Invalid literal `%s`, expecting `%s`!" % (string[:len(self.lit)], self.lit)
                return self.lit, string[len(self.lit):]
            except:
                pass

            string = string[1:]

        assert string[:len(self.lit)] == self.lit, "Invalid literal `%s`, expecting `%s`!" % (string[:len(self.lit)], self.lit)

        return self.lit, string[len(self.lit):]

    def __str__(self):
        return str(self.lit)


class key(element):
    def __init__(self, k):
        super(key, self).__init__(str(k))

        _keywords.append(k)
        self.k = str(k)

    def parse(self, string):
        a = None

        c = 0
        while len(string) > 0 and string[0] in _ignored:
            try:
                assert string[:len(self.k)] == self.k, "Invalid keyword `%s`!" % string[:len(self.k)]
                a, string = self.k, string[len(self.k):]
                break
            except:
                pass

            c += 1
            string = string[1:]

        if not a:
            assert string[:len(self.k)] == self.k, "Invalid keyword `%s`!" % string[:len(self.k)]
            a, string = self.k, string[len(self.k):]

        assert (len(string) == 0 or string[0] in _ignored or string[0] in _literals) and c > 0, "`key` object requires whitespaces around `%s`!" % self.k[1:-1]

        return a, string

    def __str__(self):
        return self.k


# Additional control structures #


# Can or not be parsed

class optional(element):
    def __init__(self, value):
        super(optional, self).__init__("")

        if not issubclass(type(value), element):
            value = liter(value)

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


# Tuple elements

class group(element):
    def __init__(self, value):
        super(group, self).__init__("")

        if not issubclass(type(value), element):
            value = liter(value)

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)
        return tuple(expand(a)), string

    def __str__(self):
        return "( " + str(self.value) + " )"


# "".join(parsed_elements)

class combine(element):
    def __init__(self, value):
        super(combine, self).__init__("")

        if not issubclass(type(value), element):
            value = liter(value)

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)
        a = expand(a)

        n = None
        for i, x in enumerate(a):
            if type(x) is dict:
                a[i] = list(x.values())[0]
                n = list(x.keys())[0]

        if n:
            return {n: "".join(a)}, string
        else:
            return "".join(a), string

    def __str__(self):
        return ">" + str(self.value) + "<"


# Counter

class count:
    """
    Count - Will initialize instance with given count that serves four kind of methods:
        - match(value) - Exactly match count of values.
        - upTo(max, value) - Match count of values between min value (initialized) and given 'max'.
        - less(value) - Will match count of values from 0 to the initialized value.
        - more(value) - Will match count of value from the initialized value and 80.
    """

    # Special object providing the count(...).more functionality

    class _moreObject(element):
        def __init__(self, cnt, value):
            super(count._moreObject, self).__init__("")

            if type(value) is str:
                value = liter(value)

            self.value = value
            self.count = cnt

        def parse(self, string):
            out = []

            i = 0
            while True:
                try:
                    a, string = self.value.parse(string)
                    out.append(a)

                    i += 1
                except:
                    break

            if self.count > i:
                raise IndexError("Expecting more than %i elements!" % self.count)

            return expand(out), string

    # Special object providing the count(...).less functionality

    class _lessObject(element):
        def __init__(self, cnt, value):
            super(count._lessObject, self).__init__("")

            if type(value) is str:
                value = liter(value)

            self.value = value
            self.count = cnt

        def parse(self, string):
            out = []

            i = 0
            while True:
                try:
                    a, string = self.value.parse(string)
                    out.append(a)

                    i += 1
                except:
                    break

            if i >= self.count:
                raise IndexError("Expecting less than %i elements!" % self.count)

            return expand(out), string

    def __init__(self, cnt):
        cnt = int(cnt)

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
        return count._lessObject(self.count, value)

    def more(self, value):
        return count._moreObject(self.count, value)


# Named output

class name(element):
    """
    Name - Is initialized with 'nam' (the dict key) and value (element which output will be used as dict value).
    """

    def __init__(self, nam, value):
        super(name, self).__init__(nam)

        if not issubclass(type(value), element):
            value = liter(value)

        self.name = nam
        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        if type(a) in [list, tuple] and len(a) == 1:
            a = a[0]

        return {self.name: a}, string

    def __str__(self):
        return "{ " + str(self.name) + ": " + str(self.value) + " }"


# Repeated named output

class repeatedDict(element):
    """
    RepeatedDict - Element that's acting like 'Name' and 'Count'. You will specify name (the output dict key),
    value (repeatedly matched elements) and keyword-arguments:
        - 'stop' - int - The max amount of matched Elements.
        - 'pre' - element - Element that will be matched at beginning, if defined.
        - 'prename' - str - Name that will be assigned as dict key to 'pre'.
    """

    def __init__(self, name, value, **kwargs):
        super(repeatedDict, self).__init__(str(value))

        name = str(name)

        if not issubclass(type(value), element):
            raise TypeError("Can't create unlimitedDict from `%s`!" % type(value))

        self.name = name
        self.value = value
        self.stop = kwargs.get("stop", -1)
        self.preparse = kwargs.get("pre", None)
        self.prename = kwargs.get("prename", self.name)

    def parse(self, string):
        out = {}

        if self.preparse:
            out[self.name], string = self.preparse.parse(string)

        i = 0
        named = False
        while True:
            try:
                assert not 0 < self.stop < i

                a, string = self.value.parse(string)

                if not named and len(out) > 0:
                    out = {self.prename: dict(out)}
                    named = True

                if len(out) > 0:
                    out = {self.name: [dict(out), a]}
                else:
                    out = {self.name: [a]}

            except:
                break

            i += 1

        return expand(out), string


# Object grouping multiple objects

class assocGroup(element):
    def __init__(self, value):
        super(assocGroup, self).__init__("")

        if not issubclass(type(value), element):
            value = liter(value)

        self.value = value

    def parse(self, string):
        a, string = self.value.parse(string)

        if type(a) not in [tuple, list]:
            a = [a]

        maxPrec = -sys.maxsize - 1

        i = 0
        while i < len(a):
            if type(a[i]) is str and a[i] in _ops:
                assoc, prec = _ops[a[i]]

                if prec > maxPrec:
                    maxPrec = prec
            i += 1

        minPrec = int(maxPrec)

        i = 0
        while i < len(a):
            if type(a[i]) is str and a[i] in _ops:
                assoc, prec = _ops[a[i]]

                if prec < minPrec:
                    minPrec = prec
            i += 1

        while maxPrec > minPrec-1:
            i = 0

            while i < len(a):
                if type(a[i]) is str and a[i] in _ops:
                    assoc, prec = _ops[a[i]]

                    if prec == maxPrec:
                        a = a[:i-1] + [tuple(a[i-1:i+2])] + a[i+2:]
                        i = 0
                        continue

                i += 1

            maxPrec -= 1

        return a, string


class lookahead(element):
    def __init__(self, value):
        super(lookahead, self).__init__("")

        if type(value) is str:
            value = liter(value)

        self.value = value

    def parse(self, string):
        return self.value.parse(string)[0], string


# Operator classes

class And(element):
    def __init__(self, first, second):
        super(And, self).__init__("")

        if not issubclass(type(first), element):
            first = liter(first)
        if not issubclass(type(second), element):
            second = liter(second)

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
        super(Or, self).__init__("")

        if not issubclass(type(first), element):
            first = liter(first)
        if not issubclass(type(second), element):
            second = liter(second)

        self.first = first
        self.second = second

    def parse(self, string):
        try:
            a, string = self.first.parse(string)
        except:
            a, string = self.second.parse(string)

        return expand(a), string

    def __str__(self):
        return "[ " + str(self.first) + " | " + str(self.second) + " ]"


class Xor(element):
    def __init__(self, first, second):
        super(Xor, self).__init__("")

        if not issubclass(type(first), element):
            first = liter(first)
        if not issubclass(type(second), element):
            second = liter(second)

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
        super(Not, self).__init__("")

        if not issubclass(type(value), element):
            value = liter(value)

        self.value = value

    def parse(self, string):
        try:
            self.value.parse(string)
        except:
            return "", string

        raise SyntaxError("Not expecting `%s` in `%s`!" % (str(self.value), string))


# TODO: !DANGER - COMPLICATED (RECURSIVE, OPERATORS) ELEMENTS!

class recurse(element):
    def __init__(self):
        super(recurse, self).__init__("")

        self.id = len(_recursed)
        _recursed[self.id] = None

    def __lshift__(self, value):
        _recursed[self.id] = value

    def parse(self, string):
        try:
            a, string = _recursed[self.id].parse(string)
        except RuntimeError:
            raise RuntimeError("Recurse element execution failed!")
        except:
            raise

        return a, string

    def __str__(self):
        return "<parse.recurse::" + str(self.id) + ">"


# Expression generator

class expression(element):
    """
    Creates expression matcher that will parse members separated by defined operators.
    member - The member (number, ...)
    lines - Operator defines with the format (operator, arity, associativity[, ternary delimiter])
    """

    def __init__(self, member, *lines, **kwargs):
        super(expression, self).__init__("")

        self.lpar = kwargs.get("lpar", liter("("))
        self.rpar = kwargs.get("rpar", liter(")"))

        lns = list(lines)
        lines = []

        for i, l in enumerate(lns):
            el, t, assoc, tern = (l + (None,))[:4]

            if not issubclass(type(el), element):
                if type(el) is str:
                    el = liter(el)
                else:
                    raise TypeError("Operator must be element, not `%s`!" % type(el))

            if assoc not in range(1, 3):
                raise TypeError("Operator association must be an integer between 1 and 2, not %i!" % assoc)

            if t not in range(1, 4):
                raise TypeError("Operator arity must be an integer between 1 and 3, not %i!" % t)
            elif t == 3:
                if not issubclass(type(tern), element):
                    tern = el

            lines.append((el, t, assoc, tern))

        self.lines = lines
        self.member = member

    def parse(self, string):
        ternOps = None
        binOps = None
        unOps = None

        for i, l in enumerate(self.lines):
            op, t, assoc, tern = l

            if t == opType.unary:
                if unOps:
                    unOps |= op
                else:
                    unOps = op

            elif t == opType.binary:
                if binOps:
                    binOps |= op
                else:
                    binOps = op

            else:
                if ternOps:
                    ternOps |= op
                else:
                    ternOps = op

            _addOp(op, [assoc, len(self.lines) - i])

        atom = recurse()

        binary = DOC_END
        unary = DOC_END

        parens = group(suppress(self.lpar) + atom + suppress(self.rpar))

        member = self.member | parens

        if unOps:
            unPars = recurse()
            unPars << group(suppress(self.lpar) + unOps + (self.member | unPars) + suppress(self.rpar))

            unary = unOps + member | unPars

            member = optional(unOps) + member

        if binOps:
            binary = member + count(1).more(binOps + member)

        atom << assocGroup(binary | unary)

        return atom.parse(string)

    def __str__(self):
        return str(self.member) + " [ " + " ".join([str(x[0]) for x in self.lines]) + " ] " + str(self.member)


DOC_END = doc_end()