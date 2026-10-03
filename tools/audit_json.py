#!/usr/bin/env python3
"""Strict JSON loading and comparison; missing keys are never null values."""
import json
import math
from pathlib import Path


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError("Non-finite JSON constant: " + value)


def loads(text):
    value = json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    validate(value)
    return value


def read(path):
    return loads(Path(path).read_text(encoding="utf-8"))


def validate(value):
    kind = type(value)
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            validate(item)
    elif kind is list:
        for item in value:
            validate(item)
    elif kind is float:
        if not math.isfinite(value):
            raise ValueError("Non-finite JSON number")
    elif kind not in (str, int, bool, type(None)):
        raise ValueError("Unsupported JSON value type: " + kind.__name__)


def differences(expected, actual):
    """Return deterministic paths, with exact key sets, array order and types."""
    validate(expected)
    validate(actual)
    errors = []

    def walk(left, right, path):
        if type(left) is not type(right):
            errors.append(path + ": type mismatch")
        elif isinstance(left, dict):
            for key in sorted(left.keys() - right.keys()):
                errors.append(path + "/" + key + ": missing key")
            for key in sorted(right.keys() - left.keys()):
                errors.append(path + "/" + key + ": unexpected key")
            for key in sorted(left.keys() & right.keys()):
                walk(left[key], right[key], path + "/" + key)
        elif isinstance(left, list):
            if len(left) != len(right):
                errors.append(path + ": array length mismatch")
            for index, (a, b) in enumerate(zip(left, right)):
                walk(a, b, path + "/" + str(index))
        elif left != right:
            errors.append(path + ": value mismatch")

    walk(expected, actual, "$")
    return errors
