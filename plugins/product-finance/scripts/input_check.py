"""Check a JSON-shaped dict against a dataclass, with plain reasons.

Standard library only. Runs on Python 3.9, so annotations use typing.Optional,
typing.Union, typing.List and typing.Dict, never `X | Y`.

`check(cls, data)` returns the object and no problems, or None and every
problem. A problem has a kind (`missing` or `invalid`), a location (field names
and list indexes), the value as given, and one reason:

    missing, not a number, not a whole number, not above N, above N,
    not one of <values>, not text, not an object, not a list

Field types the checker reads: float, int, str, a str-valued Enum, Dict[str, X],
List[X], a dataclass, and Optional[X] of any of these. Limits are declared with
`limits(gt=..., le=..., one_of=...)` and run after the type check, on the stored
value. Keys the class does not declare are ignored.
"""

import dataclasses
import enum
import typing
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T")

CHECKS: Tuple[str, ...] = ("gt", "le", "one_of")

MISSING: Any = dataclasses.MISSING

Loc = Tuple[Union[str, int], ...]


def limits(
    *,
    gt: Optional[float] = None,
    le: Optional[float] = None,
    one_of: Optional[Tuple[str, ...]] = None,
    default: Any = MISSING,
) -> Any:
    """A dataclass field carrying only the limits given."""
    given = {"gt": gt, "le": le, "one_of": one_of}
    return dataclasses.field(
        default=default, metadata={k: v for k, v in given.items() if v is not None}
    )


@dataclasses.dataclass(frozen=True)
class Problem:
    kind: str
    loc: Loc
    value: Any
    reason: str


class _Bad:
    """Marks a value that failed its check; the problem is already recorded."""


BAD = _Bad()


def _optional_inner(t: Any) -> Optional[Any]:
    """X for Optional[X], else None."""
    if typing.get_origin(t) is Union:
        rest = [a for a in typing.get_args(t) if a is not type(None)]
        if len(rest) == 1 and len(typing.get_args(t)) == 2:
            return rest[0]
    return None


def _is_text_enum(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, enum.Enum) and issubclass(t, str)


def _require_supported(t: Any, owner: str) -> None:
    """Raise TypeError for a field type the checker does not read."""
    inner = _optional_inner(t)
    if inner is not None:
        _require_supported(inner, owner)
        return
    origin, args = typing.get_origin(t), typing.get_args(t)
    if origin is list and len(args) == 1:
        _require_supported(args[0], owner)
        return
    if origin is dict and len(args) == 2 and args[0] is str:
        _require_supported(args[1], owner)
        return
    if t in (float, int, str) or _is_text_enum(t) or dataclasses.is_dataclass(t):
        return
    raise TypeError(f"unsupported field type {t!r} for {owner}")


def _whole_in_64_bits(value: float) -> bool:
    """A float pydantic takes for an int: whole, and strictly inside +-2**63."""
    return value.is_integer() and -(2**63) < value < 2**63


def _limit_reason(value: Any, meta: Any) -> Optional[str]:
    """The reason a stored number breaks its limits, or None.

    `le` is read before `gt`, as pydantic reads them: a NaN in a field with both
    limits is `above N`. Both comparisons are written so NaN fails them.
    """
    if "le" in meta and not (value <= meta["le"]):
        return f"above {meta['le']}"
    if "gt" in meta and not (value > meta["gt"]):
        return f"not above {meta['gt']}"
    return None


def _convert(t: Any, value: Any, loc: Loc, meta: Any, problems: List[Problem]) -> Any:
    """The stored value for `value` as type `t`, or BAD after recording why."""

    def bad(reason: str) -> _Bad:
        problems.append(Problem("invalid", loc, value, reason))
        return BAD

    inner = _optional_inner(t)
    if inner is not None:
        return None if value is None else _convert(inner, value, loc, meta, problems)

    origin, args = typing.get_origin(t), typing.get_args(t)
    if origin is list:
        if not isinstance(value, list):
            return bad("not a list")
        items = [_convert(args[0], v, loc + (i,), {}, problems) for i, v in enumerate(value)]
        return BAD if any(v is BAD for v in items) else items
    if origin is dict:
        if not isinstance(value, dict):
            return bad("not an object")
        pairs = {k: _convert(args[1], v, loc + (k,), {}, problems) for k, v in value.items()}
        return BAD if any(v is BAD for v in pairs.values()) else pairs
    if dataclasses.is_dataclass(t):
        obj, found = check(t, value, loc)
        problems.extend(found)
        return BAD if found else obj
    if _is_text_enum(t):
        values = [m.value for m in t]
        if isinstance(value, str) and value in values:
            return t(value)
        return bad("not one of " + ", ".join(values))
    if t is str:
        if "one_of" in meta:
            if isinstance(value, str) and value in meta["one_of"]:
                return value
            return bad("not one of " + ", ".join(meta["one_of"]))
        return value if isinstance(value, str) else bad("not text")

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return bad("not a number")
    if t is int:
        if isinstance(value, float) and not _whole_in_64_bits(value):
            return bad("not a whole number")
        stored: Union[int, float] = int(value)
    else:
        try:
            stored = float(value)
        except OverflowError:
            return bad("not a number")
    reason = _limit_reason(stored, meta)
    return bad(reason) if reason else stored


def check(cls: Type[T], data: Any, loc: Loc = ()) -> Tuple[Optional[T], List[Problem]]:
    """The object and [], or None and every problem, in field order, depth first."""
    if not isinstance(data, dict):
        return None, [Problem("invalid", loc, data, "not an object")]
    hints = typing.get_type_hints(cls)
    fields = dataclasses.fields(cls)
    for f in fields:
        _require_supported(hints[f.name], f"{cls.__name__}.{f.name}")

    problems: List[Problem] = []
    values: Dict[str, Any] = {}
    for f in fields:
        where = loc + (f.name,)
        t = hints[f.name]
        has_default = f.default is not MISSING or f.default_factory is not MISSING
        if f.name not in data:
            if not has_default:
                problems.append(Problem("missing", where, None, "missing"))
            continue
        value = data[f.name]
        if value is None and _optional_inner(t) is None:
            problems.append(Problem("missing", where, None, "missing"))
            continue
        stored = _convert(t, value, where, f.metadata, problems)
        if stored is not BAD:
            values[f.name] = stored

    if problems:
        return None, problems
    return cls(**values), []


def build(cls: Type[T], **values: Any) -> T:
    """check(cls, values); raise ValueError naming every problem."""
    obj, problems = check(cls, values)
    if problems:
        named = "; ".join(f"{'.'.join(map(str, p.loc))}: {p.reason}" for p in problems)
        raise ValueError(f"{cls.__name__}: {named}")
    return typing.cast(T, obj)
