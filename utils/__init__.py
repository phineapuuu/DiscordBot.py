from collections import OrderedDict
from datetime import datetime
from typing import Any, Callable, Iterable, List, Union
import logging

from constants import strings


l = logging.getLogger('bot')

LOG_SEP = '-' * 20


def now():
    return int(datetime.utcnow().timestamp())


TIME_FORMAT = 'UTC %H:%M:%S on %Y-%m-%d'


def format_time_interval(timestamp1: int,
                         timestamp2: int = 0,
                         *,
                         include_seconds: bool = True):
    dt = int(abs(timestamp1 - timestamp2))
    dt, seconds = dt // 60, dt % 60
    dt, minutes = dt // 60, dt % 60
    dt, hours   = dt // 24, dt % 24
    days        = dt
    s = ''
    if days:
        s += f'{days}d'
    if days or hours:
        s += f'{hours}h'
    if days or hours or minutes or not include_seconds:
        s += f'{minutes}m'
    if include_seconds:
        s += f'{seconds}s'
    return s


def format_hours(hours: int):
    days, hours = hours // 24, hours % 24
    s = ''
    if days:
        s += f'{days}d'
    s += f'{hours}h'
    return s


def human_list(words: Iterable[str], oxford_comma: bool = True):
    words = list(words)
    if len(words) == 0:
        return strings.EMPTY_LIST
    elif len(words) == 1:
        return words[0]
    s = ", ".join(words[:-1])
    if oxford_comma and len(words) > 2:
        s += ","
    s += " and " + words[-1]
    return s


def human_count(count: Union[int, float],
                singular: str,
                plural: str,
                *,
                include_number_for_singular: bool = True):
    if count == 1:
        if include_number_for_singular:
            return f"1 {singular}"
        else:
            return singular
    else:
        return f"{count} {plural}"


def sort_dict(d: dict, **kwargs):
    """Return an OrderedDict with the keys in sorted order.
    All extra keyword arguments are passed to sorted().
    """
    return OrderedDict((k, d[k]) for k in sorted(d, **kwargs))


def mutget(d: dict, keys: Union[List, Any], value=None):
    """Returns the value in a nested dictionary, setting anything undefined to
    new dictionaries except for the last one, which is set to the provided value
    if undefined. Like dict.get(), but mutates the original dictionary and can
    handle nested dictionaries/arrays.
    Arguments:
    - d -- dictionary
    - keys -- a single key or a list of keys
    - value (optional) -- default value to use if not present
    Examples:
    my_dict = {'a': {}}
    ensure_dict(my_dict, ['a', 'b', 'c'], 4)
    # The return value is 4.
    # my_dict is now {'a': {'b': {'c': 4}}.
    my_dict = {'a': {'b': {'c': 17}}}
    ensure_dict(my_dict, ['a', 'b', 'c'], 4)
    # The return value is 17.
    # my_dict does not change.
    """
    if not keys:
        return d
    if not isinstance(keys, list):
        keys = [keys]
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    if keys[-1] not in d:
        d[keys[-1]] = value
    return d[keys[-1]]


def mutset(d: dict, keys: Union[List, Any], value):
    """Sets the value in a nested dictionary, setting anything undefined to new
    dictionaries except for the last one, which is set to the provided value.
    Like mutget(), but always sets the last value.
    Examples:
    my_dict = {'a': {}}
    ensure_dict(my_dict, ['a', 'b', 'c'], 4)
    # my_dict is now {'a': {'b': {'c': 4}}.
    # This is the same as mutget().
    my_dict = {'a': {'b': {'c': 17}}}
    ensure_dict(my_dict, ['a', 'b', 'c'], 4)
    # my_dict is now {'a': {'b': 'c': 4}}.
    # This is NOT the same as mutget().
    """
    mutget(d, keys[:-1], {})[keys[-1]] = value


def lazy_mutget(d: dict, keys: Union[List, Any], value_lambda: Callable[[], Any]):
    """Like mutget(), but value is a lambda that is only evaluated if there is
    no existing value."""
    d = mutget(d, keys[:-1])
    if keys[-1] not in d:
        mutset(d, [keys[-1]], value_lambda())
    return d[keys[-1]]


INFINITY = float('inf')


def isnan(value):
    return value != value


def isinf(value):
    return abs(value) == INFINITY


def isfinite(value):
    return not (isnan(value) or isinf(value))


from .database import get_db  # noqa: E402, F401
from . import (  # noqa: E402, F401
    discord,
    error_handling,
)
