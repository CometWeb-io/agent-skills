"""Exact lexical checks for selection negative controls, never semantic grading."""
from decimal import Decimal, InvalidOperation
import re


def exact_number(text, expected):
    if not isinstance(text, str) or not isinstance(expected, str):
        return False
    value = text.strip().replace('\N{MINUS SIGN}', '-')
    if not re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]+)?', value):
        return False
    try:
        return Decimal(value) == Decimal(expected)
    except InvalidOperation:
        return False


def exact_text(text, expected):
    return isinstance(text, str) and isinstance(expected, str) and text.strip() == expected.strip()
