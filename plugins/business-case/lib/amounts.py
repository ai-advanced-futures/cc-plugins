"""Sentences, written amounts and the money scan (spec §4 Complete; rulings P3-08, P3-09, fix round 1).

`sentences` is the one splitter. `find_amounts` reads the written forms of a number in a sentence.
`money_amounts` finds every money amount in the money sections. The scan fails closed: a mark of
the case currency next to digits the grammar cannot read, or a number in a money table cell the
grammar cannot read, is reported as an unreadable amount. Nothing here raises on what a person wrote.
"""
from __future__ import annotations

import decimal
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal

from . import basis, case_doc

MONEY_SECTIONS = ("forecast", "assumptions", "financials", "baseline", "funding")
MAGNITUDES = {"k": 10**3, "thousand": 10**3, "m": 10**6, "mn": 10**6, "million": 10**6,
              "bn": 10**9, "billion": 10**9}

_SYMBOLS = tuple(sorted({s for syms in basis.CURRENCIES.values() for s in syms}, key=lambda s: (-len(s), s)))
_CODES = tuple(sorted(basis.CURRENCIES, key=lambda c: (-len(c), c)))


def _alt(tokens) -> str:
    return "|".join(re.escape(t) for t in tokens)


_MARK = _alt(sorted(set(_CODES) | set(_SYMBOLS), key=lambda t: (-len(t), t)))

# Rule (c): one table of scale tokens, each with the power of ten it names. MAGNITUDES is its subset
# the written form grammar reads after a number. `T`/`t` is a thousand only glued before a mark
# (`TEUR`, `tkr`). A known scale abbreviation code cannot read makes an amount unreadable.
_SCALES = {**{w: len(str(v)) - 1 for w, v in MAGNITUDES.items()},
           "thousands": 3, "millions": 6, "billions": 9, "mm": 6, "000": 3, "'000": 3, "000s": 3, "'000s": 3}
_BEFORE_MARK = {**_SCALES, "t": 3}
_ODD = frozenset("lakh lakhs lac lacs crore crores tn trillion trillions bil bln mio mln mrd mil thou b t".split())
_ODD_GLUED = _ODD | {"cr", "th"}
_GLUE = "|".join(sorted((w for w in _BEFORE_MARK if w.isalpha() and len(w) <= 2), key=lambda w: (-len(w), w)))
_GLUE_AFTER = "|".join(sorted((w for w in _SCALES if w.isalpha() and len(w) <= 2), key=lambda w: (-len(w), w)))
_JOIN = r"(?:[^\W\d_]|&)"  # rule (a): only a letter or `&` joins a word; `/`, `-`, `(` and space do not
_SIGNS = "(-+\u2212\u2013"  # rule (d): a sign or an opening bracket next to an amount

# Digit runs are capped: at most 15 digits before the point and 12 after, so a value has at most
# 27 significant digits and stays exact under basis.CONTEXT (28 digits). A longer run gives no form;
# next to a mark of the case currency, or in a money table cell, it is an unreadable amount.
_FORM = re.compile(
    r"(?<![^\W_])(?<![&\u00d7])(?<![0-9],)(?<![0-9]\.)(?<![0-9]')"
    rf"(?:(?P<pre>(?i:{_GLUE}))?(?:(?P<code>{_alt(_CODES)})|(?P<sym>{_alt(_SYMBOLS)}))(?P<ppost>(?i:{_GLUE_AFTER}))?[ ]?"
    r"|(?<![.])(?!(?<=[0-9][ ])[0-9]{3}(?![0-9])))"
    r"(?P<num>[0-9]{1,3}(?:,[0-9]{3}){1,4}(?:\.[0-9]{1,12})?|[0-9]{1,15}(?:\.[0-9]{1,12})?)"
    r"(?!%|[ ](?i:percent|months?|years?|customers)(?![^\W\d_]))"
    r"(?P<mag>[ ]?(?i:thousand|million|billion|bn|mn)|(?(code)[ ]?|(?(sym)[ ]?))(?i:mm|k|m))?"
    rf"(?:[ ]?(?P<spre>(?i:{_GLUE}))?(?P<suffix>{_MARK})(?![ ]?[0-9])(?!&))?"
    r"(?![^\W_])(?![.,'][0-9])(?![ ][0-9]{3}(?![0-9]))(?!\^)"
)
_LIST_MARKER = re.compile(r"(?:[-*] |[0-9]{1,9}\. )")
_FOLDED_LABELS = {label.casefold() for label in basis.LABELS}
_SEPARATOR = re.compile(r"[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*")
_DIGIT_TOKEN = re.compile(r"(?<![^\W_])\d[\d.,']*(?!%|[ ](?i:percent|months?|years?|customers)(?![^\W\d_]))")
_UNIT = re.compile(r"[ ,]*'?0{3}(?:,0{3})*s?")  # a run of zeros names a unit (`$000s`, `USD '000`), not an amount
UNREADABLE = "unreadable"  # the scale of a header that names the currency with a scale code cannot read

# Rule (b): a date or period shape is a label, never money: a year (with a month, a day, a second year
# or a letter such as `2027E`), a month name, or a period word (`Q1`, `FY`, `Yr`, `Year`, `Week` ...)
# with the number after it.
_Y4 = r"(?:19|20)[0-9]{2}"
_MON = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
        r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
_PERIOD = r"(?:q[1-4]|h[12]|fy|cy|(?:year|yr|month|mo|quarter|qtr|week|wk|period|day)s?\.?)"
_LABEL_SHAPE = re.compile(
    rf"(?<![^\W_])(?i:{_Y4}(?:[-/](?:{_Y4}|[0-9]{{1,2}}(?:[-/][0-9]{{1,2}})?)|[a-z]|[ -]?(?:q[1-4]|h[12]))?"
    rf"|[0-9]{{1,2}}[-/](?:[0-9]{{1,2}}[-/])?{_Y4}"
    rf"|[0-9]{{1,2}}[ /-]{_MON}(?:[ /'-]*(?:{_Y4}|[0-9]{{2}}))?"
    rf"|(?:{_MON}|{_PERIOD})[ /'-]*(?:{_Y4}|'?[0-9]{{1,3}})(?:[-/](?:{_Y4}|[0-9]{{1,3}}))?)(?![^\W_])")


@dataclass(frozen=True)
class Written:
    position: int
    text: str
    value: Decimal
    marked: bool


@dataclass(frozen=True)
class MoneyAmount:
    """One money amount. An unreadable one has `value` None: no figure can cover it, so the
    person rewrites it in a form the grammar reads."""
    section: str
    sentence: str
    position: int
    written: str
    value: "Decimal | None"
    unreadable: bool = False

    @property
    def anchor(self) -> str:
        digest = hashlib.sha256(self.sentence.encode("utf-8")).hexdigest()[:16]
        return f"{self.section}|{digest}|{self.position}|{self.written}"


# ---- paragraphs: prose and tables ---------------------------------------------------------------

def _is_separator(line: str) -> bool:
    return "|" in line and _SEPARATOR.fullmatch(line) is not None


def _blocks(p: str) -> list:
    """("prose", [lines], False) and ("table", [rows], has_header) in order. A table is a header line
    with `|`, its separator row, and the following lines with `|`. A run of lines starting with `|`
    and no separator row is a table with no header: every row is a body row. Separator rows are dropped."""
    lines = p.splitlines()
    out, i, n = [], 0, len(lines)

    def starts_table(j):
        return "|" in lines[j] and j + 1 < n and _is_separator(lines[j + 1]) and not _is_separator(lines[j])

    while i < n:
        line = lines[i]
        if starts_table(i) or _is_separator(line):
            header = not _is_separator(line)
            rows, i = ([line.strip()] if header else []), i + (2 if header else 1)
            while i < n and "|" in lines[i] and not starts_table(i):
                if not _is_separator(lines[i]):
                    rows.append(lines[i].strip())
                i += 1
            out.append(("table", rows, header))
        elif line.lstrip(" \t").startswith("|"):
            rows = []
            while i < n and lines[i].lstrip(" \t").startswith("|") and not starts_table(i) and not _is_separator(lines[i]):
                rows.append(lines[i].strip())
                i += 1
            out.append(("table", rows, False))
        else:
            if out and out[-1][0] == "prose":
                out[-1][1].append(line)
            else:
                out.append(("prose", [line], False))
            i += 1
    return [block for block in out if block[1]]


def _starts_unit(line: str):
    """(True, the line without its list marker) when the line starts a new unit, else (False, line)."""
    m = _LIST_MARKER.match(line)
    if m:
        return True, line[m.end():]
    head, sep, _ = line.partition(":")
    return bool(sep) and head.casefold() in _FOLDED_LABELS, line


def _split_prose(unit: str) -> list:
    out, start = [], 0
    for m in re.finditer(r"[.!?] ", unit):
        nxt = unit[m.end():]
        if nxt[:1].isupper() or nxt[:1] in tuple("0123456789") or nxt.startswith(_SYMBOLS):
            out.append(unit[start:m.end() - 1])
            start = m.end()
    out.append(unit[start:])
    return [s for s in (part.strip() for part in out) if s]


def _prose_sentences(lines: list) -> list:
    units = []
    for line in lines:
        line = line.lstrip(" \t")
        new, rest = _starts_unit(line)
        if new or not units:
            units.append([rest])
        else:
            units[-1].append(rest)
    out = []
    for unit in units:
        out.extend(_split_prose(case_doc.normalize("\n".join(unit))))
    return out


def _paragraph_sentences(p: str) -> list:
    out = []
    for kind, items, _ in _blocks(p):
        out.extend(items if kind == "table" else _prose_sentences(items))
    return out


def sentences(body: str) -> list:
    """The sentences of a section body: table rows, list items, basis lines, then prose split after . ! ?"""
    out = []
    for p in case_doc.paragraphs(body):
        out.extend(_paragraph_sentences(p))
    return out


# ---- written amounts ----------------------------------------------------------------------------

def _owns(token: str, currency: str) -> bool:
    return token == currency or token in basis.CURRENCIES.get(currency, ())


def _plain(value: Decimal) -> Decimal:
    """The value with no trailing zeros after the point and no exponent: $0.5m gives 500000."""
    if value == value.to_integral_value():
        return value.quantize(Decimal(1))
    return value.normalize()


def _scan(sentence: str, currency) -> list:
    """(Written, kind, end) for each written form, left to right. kind is "case" (only the case
    currency's marks, or a magnitude), "other" (only another currency's marks), "mixed" (both: an
    unreadable amount), or "none" (no mark)."""
    out = []
    for m in _FORM.finditer(sentence):
        marks = [t for t in (m.group("code"), m.group("sym"), m.group("suffix")) if t]
        scales = [t.strip().casefold() for t in (m.group("pre"), m.group("ppost"), m.group("mag"), m.group("spre")) if t]
        ours = [t for t in marks if currency is not None and _owns(t, currency)]
        if currency is not None and marks and not ours:
            kind = "other"
        elif (ours and len(ours) < len(marks)) or len(scales) > 1:
            kind = "mixed"
        else:
            kind = "case" if (ours or scales) else "none"
        with decimal.localcontext(basis.CONTEXT):
            value = Decimal(m.group("num").replace(",", ""))
            if scales:
                value = value * 10 ** _BEFORE_MARK[scales[0]]
            value = _plain(value)
        out.append((Written(m.start(), m.group(0), value, kind == "case"), kind, m.end()))
    return out


def find_amounts(sentence: str, currency) -> list:
    return [w for w, _, _ in _scan(sentence, currency)]


def amount_at(sentence: str, position: int, currency):
    for w in find_amounts(sentence, currency):
        if w.position == position:
            return w
    return None


# ---- unreadable amounts -------------------------------------------------------------------------

def _case_marks(currency) -> list:
    return sorted({currency, *basis.CURRENCIES.get(currency, ())}, key=lambda t: (-len(t), t))


def _letter_before_is_attached(sentence: str, start: int) -> bool:
    """A mark may follow letters only when those letters follow a digit (`5MMR`) or are a scale
    glued to it (`kUSD`), never `US$`."""
    i = start
    while i > 0 and sentence[i - 1].isalpha():
        i -= 1
    return i > 0 and sentence[i - 1].isdigit() or sentence[i:start].casefold() in _BEFORE_MARK


_GROWS = ".,')\u00d7" + _SIGNS


def _grow_right(s: str, b: int) -> int:
    """Past one space, then over letters, digits, `.,'` and a space between two digits."""
    if b < len(s) and s[b].isspace():
        b += 1
    while b < len(s):
        c = s[b]
        if c.isalnum() or c in _GROWS or (c.isspace() and s[b - 1].isdigit() and s[b + 1:b + 2].isdigit()):
            b += 1
        else:
            break
    return b


def _grow_left(s: str, a: int) -> int:
    if a > 0 and s[a - 1].isspace():
        a -= 1
    while a > 0:
        c = s[a - 1]
        if c.isalnum() or c in _GROWS or (c.isspace() and a >= 2 and s[a - 2].isdigit() and s[a].isdigit()):
            a -= 1
        else:
            break
    return a


def _trim(raw: str) -> str:
    """Sentence punctuation and a closing bracket the form did not open are not part of it."""
    while raw and (raw[-1] in ".," or (raw[-1] == ")" and raw.count("(") < raw.count(")"))):
        raw = raw[:-1]
    return raw


def _unread_span(sentence: str, start: int, end: int):
    """The span of an unread form around the mark at [start, end), or None if no digit is next to it."""
    after = re.match(rf"\s?[{re.escape(_SIGNS)}]?\s?\.?\d", sentence[end:])
    before = re.search(r"\d[^\W\d_]*\)?\s?\Z", sentence[:start])
    if not after and not before:
        return None
    b = _grow_right(sentence, end) if after else end
    a = _grow_left(sentence, start) if before else start
    raw = _trim(sentence[a:b])
    return (a, a + len(raw)) if raw else None


def _unreadable_marks(sentence: str, currency, read: list) -> list:
    """(start, end) of each case-currency mark next to digits that no written form read."""
    if currency is None:
        return []
    spans = [(w.position, end) for w, _, end in read]
    out = []
    pattern = rf"(?<!&)(?:{_alt(_case_marks(currency))})(?i:{_GLUE_AFTER})?(?!{_JOIN})"
    for m in re.finditer(pattern, sentence):
        if any(a <= m.start() < b for a, b in spans + out):
            continue
        if m.start() > 0 and sentence[m.start() - 1].isalpha() and not _letter_before_is_attached(sentence, m.start()):
            continue
        span = _unread_span(sentence, m.start(), m.end())
        rest = (sentence[span[0]:m.start()] + sentence[m.end():span[1]]).strip(" (),") if span else ""
        if span and not (_UNIT.fullmatch(rest) or _numeric_power(rest) in (3, 6, 9)):
            out.append(span)
    return out


# ---- the money scan -----------------------------------------------------------------------------

_AFFIX = re.compile(r"[^\W\d_]+|'?0{3}(?:,0{3})*s?|")
_CELL_TOKEN = re.compile(r"(?<![^\W_&])[^\W\d_]+(?:&[^\W\d_]+)*(?![^\W_&])"
                         r"|(?<![\w.,'])(?:[x\u00d7][ ]?)?'?[0-9](?:[\w^]|[.,][0-9])*")
_RATE = re.compile(r"(?:/[ ]*|(?<![^\W_])(?i:per)[ ]+)\Z")  # rule (c'): `/m`, `per M`: a rate unit, not a scale
# R-4: in a money cell, a scale word one space after an unmarked number scales it (`5.2 m`), as it
# does after a marked number in prose (`$5.2 m`). Unmarked prose (`1.2 m`) is not money, so may be metres.
_SPACED_SCALE = re.compile(r"[ ](?i:(mm|k|m))(?![^\W_])")


def _numeric_power(token: str):
    """Rule (c'): the power a numeric scale token names (`'000`, `000s`, `1000s`, `1,000,000s`,
    `x1000`, `×1,000`), else UNREADABLE."""
    t = token.casefold()
    times = t[:1] in "x\u00d7"
    t = t.lstrip("x\u00d7 ").lstrip("'")
    digits = t[:-1] if t.endswith("s") else t
    if re.fullmatch(r"0{3}", digits) or (t.endswith("s") or times) and re.fullmatch(r"1(?:,?000){1,3}", digits):
        return len(digits.replace(",", "")) - 1 if digits[0] == "1" else 3
    return UNREADABLE


def _power(token: str, table: dict, odd: frozenset):
    """The power of ten a scale token names, UNREADABLE for a scale code cannot read, else None."""
    t = token.casefold()
    if t in table:
        return table[t]
    return UNREADABLE if t in odd or t[:1] in "'01" else None


def _currency_scale(cell: str, currency):
    """The scale of a cell that names the case currency (rule c): 1, a power of ten, or UNREADABLE;
    None when the cell does not name it. A mark is the code (any case) or a symbol, not inside a
    longer mark of another currency, and joined to no letter or `&` (rule a) except a scale token
    glued to it (`kUSD`, `TEUR`, `$m`, `$000s`). The scale is the one scale token anywhere in the
    cell; none gives 1; two, or a scale code cannot read, give UNREADABLE."""
    if currency is None:
        return None
    foreign = [m.span() for m in re.finditer(_MARK, cell) if not _owns(m.group(), currency)]
    marks = [(re.escape(currency), re.IGNORECASE)] + [(re.escape(sym), 0) for sym in basis.CURRENCIES[currency]]
    powers, rest, named = [], cell, False
    for pattern, flags in marks:
        for m in re.finditer(pattern, cell, flags):
            a, b = m.span()
            if any(fa <= a and b <= fb and fb - fa > b - a for fa, fb in foreign):
                continue
            pre, post = re.search(r"[^\W\d_]*\Z", cell[:a]).group(), _AFFIX.match(cell, b).group()
            glued = [_power(pre, _BEFORE_MARK, _ODD_GLUED) if pre else 0,
                     _power(post, _SCALES, _ODD_GLUED) if post else 0]
            if None in glued or cell[a - len(pre) - 1:a - len(pre)] == "&" or cell[b + len(post):][:1] == "&":
                continue
            named = True
            powers += [p for p, part in zip(glued, (pre, post)) if part]
            rest = rest[:a - len(pre)] + " " * (len(pre) + b - a + len(post)) + rest[b + len(post):]
    if not named:
        return None
    for m in _LABEL_SHAPE.finditer(rest):
        rest = rest[:m.start()] + " " * len(m.group()) + rest[m.end():]
    amounts = [(w.position, end) for w, kind, end in _scan(cell, currency)  # a cell that IS an amount
               if kind == "case" and w.text == cell.strip() and not _UNIT.fullmatch(_number(w.text))]
    for t in _CELL_TOKEN.finditer(rest):
        numeric = re.search(r"[0-9]", t.group())
        p = _numeric_power(t.group()) if numeric else _power(t.group(), _SCALES, _ODD)
        if numeric and p == UNREADABLE and any(a <= numeric.start() + t.start() < b for a, b in amounts):
            continue  # the digits of a cell that is an amount (`$1,200,000`) are not label text
        if p is not None and not (p != UNREADABLE and _RATE.search(rest[:t.start()])):
            powers.append(p)
    if UNREADABLE in powers or len(powers) > 1:
        return UNREADABLE
    return 10 ** powers[0] if powers else 1


def _cells(row: str) -> list:
    inner = row[1:] if row.startswith("|") else row
    inner = inner[:-1] if inner.endswith("|") else inner
    return inner.split("|")


def _column(row: str, position: int) -> int:
    return row[:position].count("|") - (1 if row.startswith("|") else 0)


def _number(text: str) -> str:
    """The digits of a written form, with its marks and magnitude taken off."""
    m = re.search(r"'?[0-9][0-9,.]*s?", text)
    return m.group(0) if m else text


def _signed(sentence: str, start: int, end: int):
    """Rule (d'): the span of an amount with a sign right before it (a sign must not follow a letter
    or digit, so `$5-$6` is a range), or wrapped in brackets: `(` right before it counts only when
    `)` closes right after it, so `($5k per month)` reads and `($5,000)` does not. Else None."""
    a = start
    while a > 0 and sentence[a - 1] in _SIGNS:
        a -= 1
    closed = sentence[end:end + 1] == ")"
    if "(" in sentence[a:start] and not closed:
        a += sentence[a:start].rindex("(") + 1
    if a == start or ("(" not in sentence[a:start] and a > 0 and sentence[a - 1].isalnum()):
        return None
    return a, end + closed


def _amounts_in(section: str, sentence: str, currency, money_cell) -> list:
    """The money amounts of one sentence. `money_cell(position)` gives the scale of the money table
    cell at a position (1, a power of ten or UNREADABLE), or None when the position is not in one;
    prose passes a function that always gives None. An unmarked number in a money cell takes the
    cell's scale, unless it sits in a date or period shape (rule b)."""
    read = _scan(sentence, currency)
    labels = [m.span() for m in _LABEL_SHAPE.finditer(sentence)]

    def inside(p, spans):
        return any(a <= p < b for a, b in spans)

    unread = [(w.position, end) for w, kind, end in read if kind == "mixed"]
    unread += _unreadable_marks(sentence, currency, read)
    found = []
    for w, kind, end in read:
        if kind in ("other", "mixed") or _UNIT.fullmatch(_number(w.text)):
            continue
        scale = 1 if w.marked else money_cell(w.position)
        if scale is None or (not w.marked and inside(w.position, labels)):
            continue
        spaced = None if w.marked else _SPACED_SCALE.match(sentence, end)
        if spaced:
            end = spaced.end()
            if scale != 1:  # the header's scale and the cell's own: two scales fail closed
                scale = UNREADABLE
            else:
                with decimal.localcontext(basis.CONTEXT):
                    value = w.value * 10 ** _SCALES[spaced.group(1).casefold()]
                w = Written(w.position, sentence[w.position:end], value, True)
        signed = _signed(sentence, w.position, end)
        if signed or scale == UNREADABLE:
            unread.append(signed or (w.position, end))
        else:
            found.append((w, end, scale))
    spans = [(w.position, end) for w, _, end in read]
    for m in _DIGIT_TOKEN.finditer(sentence):
        if money_cell(m.start()) is not None and not inside(m.start(), spans + unread + labels):
            raw = _trim(sentence[m.start():_grow_right(sentence, m.start())])
            if not _UNIT.fullmatch(raw):
                unread.append(_signed(sentence, m.start(), m.start() + len(raw)) or (m.start(), m.start() + len(raw)))
    out = []
    for w, end, scale in found:
        if not any(a < end and w.position < b for a, b in unread):
            with decimal.localcontext(basis.CONTEXT):
                out.append(MoneyAmount(section, sentence, w.position, w.text, _plain(w.value * scale)))
    out += [MoneyAmount(section, sentence, a, sentence[a:b], None, True) for a, b in unread]
    return sorted(out, key=lambda m: m.position)


_BARE_NUMBER = re.compile(r"[0-9][0-9.,' ]*(?:[ ]?(?i:mm|k|m|bn|mn|thousand|million|billion))?")


def _whole_amount(cell: str, currency) -> bool:
    """NB-C: whether a header-row cell is data, that is its whole content (signs and brackets aside)
    is a number or one written amount. `Option 1`, `10 seats` and `Release 2.0` are labels."""
    core = cell.strip().strip(_SIGNS + ") ").strip()
    if _BARE_NUMBER.fullmatch(core):
        return True
    return any(w.text == core and kind != "none" for w, kind, _ in _scan(core, currency))


def _table_money(section: str, rows: list, header: bool, currency) -> list:
    """A cell of the first row that names the currency makes its column money, with its scale; this
    holds for a pipe run with no separator row too. A row whose first cell names the currency is
    money (but for that first cell), with that cell's scale; a corner cell that names it does the
    same for every row. In a money cell every number is money except a date or period shape. The
    header row (when there is a separator row) gives only marked amounts, unless its first cell
    names the currency (rule b'), and then only a cell that is a number or an amount (NB-C). A cell
    that itself names the currency is label text: only its marked amounts count."""
    first = _cells(rows[0])
    columns = {j: _currency_scale(cell, currency) for j, cell in enumerate(first)}
    columns = {j: scale for j, scale in columns.items() if scale is not None}
    labels_only = header and 0 not in columns
    out = []
    for i, row in enumerate(rows):
        row_scale = _currency_scale(_cells(row)[0], currency)
        if row_scale is None:
            row_scale = columns.get(0)

        names = [_currency_scale(cell, currency) is not None for cell in _cells(row)]
        if header and i == 0:  # NB-C: a header cell is data only when it is a number or an amount
            names = [n or not _whole_amount(cell, currency) for n, cell in zip(names, _cells(row))]

        def money_cell(position, row=row, row_scale=row_scale, names=names, quiet=labels_only and i == 0):
            col = _column(row, position)
            if quiet or names[col]:
                return None
            if col in columns:
                return columns[col]
            return row_scale if col != 0 else None

        out.extend(_amounts_in(section, row, currency, money_cell))
    return out


def money_amounts(sections: dict, currency) -> list:
    """Every money amount in the money sections, in section order, then sentence order (spec §4).

    Tables: see `_table_money`."""
    out = []
    for section in MONEY_SECTIONS:
        body = sections.get(section)
        if body is None:
            continue
        for p in case_doc.paragraphs(body):
            for kind, items, header in _blocks(p):
                if kind == "table":
                    out.extend(_table_money(section, items, header, currency))
                    continue
                for s in _prose_sentences(items):
                    out.extend(_amounts_in(section, s, currency, lambda position: None))
    return out
