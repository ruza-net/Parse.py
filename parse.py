__author__ = 'Jan Růžička <jan.ruzicka01@gmail.com>'
__version__ = "1.0.1"

from utils import *
import sys
import re


_ignored = " "

_recursed = {}

_keywords = []
_literals = []

_ops = {}


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

        t = kwargs.get("type", liter)

        stop = kwargs.get("stop", None)

        self.sep = t(kwargs.get("sep", ","))

        self.cut = kwargs.get("cut", True)
        self.suppress = kwargs.get("suppress", True)

        self.min = kwargs.get("min", -1)
        self.max = kwargs.get("max", -1)

        if stop:
            self.stop = t(stop)
        else:
            self.stop = None

        if not issubclass(type(value), element):
            value = liter(value)
        if type(self.sep) is str:
            self.sep = liter(self.sep)

        self.value = value

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

        assert len(out) > self.min, "Minimal length %i not humbled!" % self.min
        assert len(out) < self.max or self.max == -1, "Maximal length %i humbled!" % self.max

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
        if string[0] not in self.chars:
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
        a = re.match(self.exp, string)

        if not a:
            while len(string) > 0 and string[0] in _ignored:
                a = re.match(self.exp, string)

                if a:
                    break

                string = string[1:]

            if not a:
                a = re.match(self.exp, string)

                if not a:
                    raise SyntaxError("Regex evaluation fault!")

        return [a.group(0)], string[len(a.group(0)):]

    def __str__(self):
        return repr(str(self.exp))


class liter(element):
    def __init__(self, lit):
        super(liter, self).__init__(lit)

        if lit not in _keywords:
            _literals.append(lit)

        self.lit = lit

    def parse(self, string):
        if string[:len(self.lit)] != self.lit:
            while len(string) > 0 and string[0] in _ignored and string[:len(self.lit)] != self.lit:
                string = string[1:]

            assert string[:len(self.lit)] == self.lit, "Invalid literal `%s`, expecting `%s`!" % (string[:len(self.lit)], self.lit)

        return self.lit, string[len(self.lit):]

    def __str__(self):
        return "'" + str(self.lit) + "'"


class key(element):
    def __init__(self, k):
        super(key, self).__init__(str(k))

        _keywords.append(k)
        self.k = liter(k)

    def parse(self, string):
        a = None

        c = 0
        while len(string) > 0 and string[0] in _ignored:
            try:
                a, string = self.k.parse(string)
            except:
                pass

            c += 1
            string = string[1:]

        if not a:
            a, string = self.k.parse(string)

        assert (len(string) == 0 or string[0] in _ignored or string[0] in _literals) and c > 0, "`key` object requires whitespaces around `%s`!" % self.k[1:-1]

        return a, string

    def __str__(self):
        return str(self.k)[1:-1]


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
        return "".join(expand(a)), string

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
        tmp = count(0)

        return tmp.upTo(self.count, value)

    def more(self, value):
        if self.count < 1:
            return optional(self.upTo(80, value))
        else:
            return self.upTo(80, value)


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
    def __init__(self, member, *lines, **kwargs):
        super(expression, self).__init__("")

        self.lpar = kwargs.get("lpar", liter("("))
        self.rpar = kwargs.get("rpar", liter(")"))

        lns = list(lines)
        lines = []

        for i, l in enumerate(lns):
            el, prec, assoc, t, tern = (l + (opType.binary,None))[:5]

            if not issubclass(type(el), element):
                if type(el) is str:
                    el = liter(el)
                else:
                    raise TypeError("Operator must be element, not `%s`!" % type(el))

            if type(prec) is not int:
                raise TypeError("Operator precedence must be an integer, not `%s`!" % type(prec))

            if assoc not in range(1, 3):
                raise TypeError("Operator association must be an integer between 1 and 2, not %i!" % assoc)

            if prec > len(lns)-1:
                print("Given operator precedence is greater that the maximal (%i, Number of operators - 1)." % len(lns)-1)

                prec = len(lns) - 1

            if t not in range(1, 4):
                raise TypeError("Operator type must be an integer between 1 and 3, not %i!" % t)
            elif t == 3:
                if not issubclass(type(tern), element):
                    tern = el

            lines.append((el, prec, assoc, t, tern))

        self.lines = lines
        self.member = member

    def parse(self, string):
        rule = None

        ternOps = None
        binOps = None
        unOps = None

        for l in self.lines:
            op, prec, assoc, t, tern = (l + (opType.binary,None))[:5]

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

            if type(op) in [And, Or, Xor, Not]:
                _ops[str(op.first)[1:-1]] = [assoc, prec]
                _ops[str(op.second)[1:-1]] = [assoc, prec]
            else:
                _ops[str(op)[1:-1]] = [assoc, prec]

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
            cont = optional(count(1).more(binOps + member))
            binary = member + binOps + member + cont

        atom << (unary | binary)
        rule = assocGroup(atom)

        return rule.parse(string)


DOC_END = doc_end()