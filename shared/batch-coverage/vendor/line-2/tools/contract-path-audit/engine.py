#!/usr/bin/env python3
"""Exact-decimal JSON structural contracts; offline, standard library only."""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import os
import stat
import json
import re
import sys

KEYS = {"type", "required", "properties", "additionalProperties", "items",
        "minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum",
        "enum", "pattern", "prefixItems", "uniqueItems"}
TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


class ContractError(ValueError):
    pass


def pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def same(a, b):
    # JSON boolean true must not compare equal to the JSON number 1.
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if type(a) in (int, Decimal) and type(b) in (int, Decimal):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def prepare(c, path=""):
    """Reject misspelled, unsupported and contradictory contract rules."""
    def fail(message):
        raise ContractError(f"contract {path or '/'}: {message}")
    if not isinstance(c, dict):
        fail("must be an object")
    if set(c) - KEYS:
        fail("unsupported rules: " + ", ".join(sorted(set(c) - KEYS)))
    t = c.get("type")
    if not isinstance(t, str) or t not in TYPES:
        fail("type must name one supported JSON type")
    permitted = {"type", "enum"}
    permitted |= {"object": {"properties", "required", "additionalProperties"},
                  "array": {"items", "minItems", "maxItems", "prefixItems", "uniqueItems"},
                  "string": {"minLength", "maxLength", "pattern"},
                  "number": {"minimum", "maximum"},
                  "integer": {"minimum", "maximum"}}.get(t, set())
    if set(c) - permitted:
        fail("rules incompatible with type: " + ", ".join(sorted(set(c) - permitted)))
    if "enum" in c and (not isinstance(c["enum"], list) or not c["enum"]):
        fail("enum must be a nonempty array")
    for lo, hi in (("minItems", "maxItems"), ("minLength", "maxLength"), ("minimum", "maximum")):
        for k in (lo, hi):
            if k in c:
                v = c[k]
                if type(v) not in (int, Decimal) or (type(v) is Decimal and not v.is_finite()):
                    fail(k + " must be a finite number")
                if k not in ("minimum", "maximum") and (type(v) is not int or v < 0):
                    fail(k + " must be a nonnegative integer")
        if lo in c and hi in c and c[lo] > c[hi]:
            fail(lo + " exceeds " + hi)
    if "pattern" in c:
        if not isinstance(c["pattern"], str):
            fail("pattern must be a string")
        try:
            re.compile(c["pattern"])
        except re.error as exc:
            fail("invalid Python regular expression: " + str(exc))
    if t == "object":
        props = c.get("properties", {})
        required = c.get("required", [])
        if not isinstance(props, dict):
            fail("properties must be an object")
        if not isinstance(required, list) or any(not isinstance(k, str) for k in required):
            fail("required must be an array of property names")
        if len(required) != len(set(required)) or any(k not in props for k in required):
            fail("required names must be unique and declared in properties")
        if "additionalProperties" in c and type(c["additionalProperties"]) is not bool:
            fail("additionalProperties must be boolean")
        for k, child in props.items():
            prepare(child, pointer(path, k))
    if "items" in c:
        prepare(c["items"], pointer(path, "items"))
    if "prefixItems" in c:
        if not isinstance(c["prefixItems"], list):
            fail("prefixItems must be an array of contracts")
        for i, child in enumerate(c["prefixItems"]):
            prepare(child, pointer(pointer(path, "prefixItems"), i))
    if "uniqueItems" in c and type(c["uniqueItems"]) is not bool:
        fail("uniqueItems must be boolean")
    return c


def validate(value, c, path=""):
    errors = []
    def add(rule, message, at=path):
        errors.append({"path": at, "rule": rule, "message": message})
    t = c["type"]
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "boolean": type(value) is bool,
             "null": value is None, "integer": type(value) is int,
             "number": type(value) in (int, Decimal)}[t]
    if not valid:
        add("type", "expected " + t)
        return errors
    if "enum" in c and not any(same(value, x) for x in c["enum"]):
        add("enum", "value is not an allowed choice")
    if t == "object":
        props = c.get("properties", {})
        for k in c.get("required", []):
            if k not in value:
                add("required", "missing property", pointer(path, k))
        for k, v in value.items():
            if k in props:
                errors.extend(validate(v, props[k], pointer(path, k)))
            elif c.get("additionalProperties", True) is False:
                add("additionalProperties", "unexpected property", pointer(path, k))
    elif t in ("string", "array"):
        lo, hi = ("minLength", "maxLength") if t == "string" else ("minItems", "maxItems")
        if lo in c and len(value) < c[lo]:
            add(lo, f"length must be at least {c[lo]}")
        if hi in c and len(value) > c[hi]:
            add(hi, f"length must be at most {c[hi]}")
        if t == "string" and "pattern" in c and re.search(c["pattern"], value) is None:
            add("pattern", "does not match the required pattern")
        if t == "array" and "items" in c:
            for i in range(len(c.get("prefixItems", [])), len(value)):
                v = value[i]
                errors.extend(validate(v, c["items"], pointer(path, i)))
        if t == "array":
            for i, child in enumerate(c.get("prefixItems", [])):
                if i < len(value):
                    errors.extend(validate(value[i], child, pointer(path, i)))
            if c.get("uniqueItems", False):
                for i, v in enumerate(value):
                    earlier = next((j for j in range(i) if same(v, value[j])), None)
                    if earlier is not None:
                        add("uniqueItems", f"duplicates item at {pointer(path, earlier)}",
                            pointer(path, i))
    elif t in ("number", "integer"):
        for k, fails in (("minimum", lambda x: value < x), ("maximum", lambda x: value > x)):
            if k in c and fails(c[k]):
                add(k, f"must respect {k} {c[k]}")
    return errors


MAX_BYTES = 1_000_000


def read_bytes(name, limit=MAX_BYTES):
    """Traverse relative paths by directory descriptors; never follow symlinks."""
    if not isinstance(name, str) or not name or name.startswith('/'):
        raise ValueError('input must be a relative workspace path')
    parts = name.split('/')
    if any(not p or p.startswith('.') for p in parts):
        raise ValueError('empty, hidden and parent path components are refused')
    if type(limit) is not int or not 0 <= limit <= MAX_BYTES:
        raise ValueError('invalid byte limit')
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValueError('POSIX no-follow directory reads are required')
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    file_fd = None
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=directory)
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError('input must be a regular file')
        if metadata.st_size > limit:
            raise ValueError(f'input exceeds {limit} bytes')
        chunks = []
        remaining = limit + 1
        while remaining:
            block = os.read(file_fd, min(65536, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        data = b''.join(chunks)
        if len(data) > limit:
            raise ValueError(f'input exceeds {limit} bytes')
        return data
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory)


def decode(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError("duplicate JSON property: " + key)
            result[key] = value
        return result
    def numeric(token, integer=False):
        if len(token) > 4096:
            raise ValueError("numeric token exceeds 4096 characters")
        if integer:
            return int(token)
        try:
            value = Decimal(token)
        except InvalidOperation:
            raise ValueError("unsupported decimal token")
        if not value.is_finite() or abs(value.as_tuple().exponent) > 1000000:
            raise ValueError("decimal exponent exceeds supported range")
        return value
    def reject(token):
        raise ValueError("invalid JSON constant: " + token)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_int=lambda t: numeric(t, True), parse_float=numeric,
                      parse_constant=reject)


def inspect(contract_raw, document_raw):
    contract = prepare(decode(contract_raw))
    errors = validate(decode(document_raw), contract)
    return {"valid": not errors, "complete": True, "errors": errors,
            "numeric_semantics": "exact decimal; integer requires an integer literal",
            "sources": {"contract": {"sha256": hashlib.sha256(contract_raw).hexdigest(),
                                      "bytes": len(contract_raw)},
                        "document": {"sha256": hashlib.sha256(document_raw).hexdigest(),
                                      "bytes": len(document_raw)}}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract")
    parser.add_argument("document")
    for role in ("contract", "document"):
        parser.add_argument("--" + role + "-sha256")
    args = parser.parse_args(argv)
    try:
        # Capture each lexical path once, check both pins before interpreting JSON.
        captured = {}
        for name in (args.contract, args.document):
            if name not in captured:
                captured[name] = read_bytes(name)
        for role in ("contract", "document"):
            pin = getattr(args, role + "_sha256")
            if pin is not None:
                if not re.fullmatch("[0-9a-f]{64}", pin):
                    raise ValueError("expected SHA-256 must be 64 lowercase hex digits")
                if hashlib.sha256(captured[getattr(args, role)]).hexdigest() != pin:
                    raise ValueError(role + " SHA-256 mismatch")
        result = inspect(captured[args.contract], captured[args.document])
        output = json.dumps(result, ensure_ascii=True, indent=2)
        if len(output.encode("utf-8")) > 1000000:
            raise ValueError("complete diagnostic output exceeds 1000000 bytes")
        print(output)
        return 0 if result["valid"] else 1
    except (ValueError, OSError, RecursionError, InvalidOperation) as exc:
        print(json.dumps({"valid": False, "complete": False,
                          "error": str(exc)[:1000]}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
