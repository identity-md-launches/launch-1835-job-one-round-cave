#!/usr/bin/env python3
"""Check a JSON document and audit which contract nodes it actually exercised."""

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import sys

import engine


def type_matches(value, expected):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: type(value) is int,
        "number": lambda: type(value) in (int, Decimal),
        "boolean": lambda: type(value) is bool,
        "null": lambda: value is None,
    }[expected]()


def audit(contract, document):
    """Return structural diagnostics and node coverage from one parsed pair."""
    engine.prepare(contract)
    nodes = []
    by_path = {}

    def declare(rule, path, parent=None, route=None):
        node = {
            "contractPath": path,
            "type": rule["type"],
            "rules": sorted(k for k in rule if k not in
                            ("type", "properties", "items", "prefixItems")),
            "visits": 0,
            "typePasses": 0,
            "sampleDocumentPaths": [],
        }
        nodes.append(node)
        by_path[path] = (node, parent, route)
        if rule["type"] == "object":
            for name, child in rule.get("properties", {}).items():
                child_path = engine.pointer(engine.pointer(path, "properties"), name)
                declare(child, child_path, path, ("property", name))
        elif rule["type"] == "array":
            for index, child in enumerate(rule.get("prefixItems", [])):
                child_path = engine.pointer(engine.pointer(path, "prefixItems"), index)
                declare(child, child_path, path, ("prefix", index))
            if "items" in rule:
                declare(rule["items"], engine.pointer(path, "items"), path,
                        ("items", len(rule.get("prefixItems", []))))

    def visit(rule, value, contract_path, document_path):
        node = by_path[contract_path][0]
        node["visits"] += 1
        if len(node["sampleDocumentPaths"]) < 3:
            node["sampleDocumentPaths"].append(document_path)
        if not type_matches(value, rule["type"]):
            return
        node["typePasses"] += 1
        if rule["type"] == "object":
            for name, child in rule.get("properties", {}).items():
                if name in value:
                    visit(child, value[name],
                          engine.pointer(engine.pointer(contract_path, "properties"), name),
                          engine.pointer(document_path, name))
        elif rule["type"] == "array":
            prefixes = rule.get("prefixItems", [])
            for index, item in enumerate(value):
                if index < len(prefixes):
                    child = prefixes[index]
                    child_path = engine.pointer(engine.pointer(contract_path, "prefixItems"), index)
                elif "items" in rule:
                    child = rule["items"]
                    child_path = engine.pointer(contract_path, "items")
                else:
                    continue
                visit(child, item, child_path, engine.pointer(document_path, index))

    declare(contract, "")
    visit(contract, document, "", "")

    for node in nodes:
        path = node["contractPath"]
        parent, route = by_path[path][1:]
        if node["visits"] and node["typePasses"]:
            node["status"] = "exercised"
        elif node["visits"]:
            node["status"] = "type_rejected"
        else:
            node["status"] = "dormant"
            if parent is None:
                raise AssertionError("root is always visited")
            parent_node = by_path[parent][0]
            if parent_node["visits"] == 0:
                node["reason"] = "parent_dormant"
            elif parent_node["typePasses"] == 0:
                node["reason"] = "parent_type_rejected"
            else:
                node["reason"] = {
                    "property": "property_absent",
                    "prefix": "array_too_short",
                    "items": "no_tail_items",
                }[route[0]]

    errors = engine.validate(document, contract)
    return {
        "complete": True,
        "valid": not errors,
        "counts": {
            "declaredNodes": len(nodes),
            "exercised": sum(n["status"] == "exercised" for n in nodes),
            "typeRejected": sum(n["status"] == "type_rejected" for n in nodes),
            "dormant": sum(n["status"] == "dormant" for n in nodes),
            "violations": len(errors),
        },
        "nodes": nodes,
        "errors": errors,
    }


def inspect(contract_raw, document_raw, contract_pin=None, document_pin=None):
    digests = (hashlib.sha256(contract_raw).hexdigest(),
               hashlib.sha256(document_raw).hexdigest())
    for role, pin, digest in (("contract", contract_pin, digests[0]),
                              ("document", document_pin, digests[1])):
        if pin is not None:
            if re.fullmatch(r"[0-9a-f]{64}", pin) is None:
                raise ValueError(role + " SHA-256 pin must be 64 lowercase hex digits")
            if pin != digest:
                raise ValueError(role + " SHA-256 mismatch")
    contract = engine.decode(contract_raw)
    document = engine.decode(document_raw)
    result = audit(contract, document)
    result["sources"] = {
        "contract": {"sha256": digests[0], "bytes": len(contract_raw)},
        "document": {"sha256": digests[1], "bytes": len(document_raw)},
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract")
    parser.add_argument("document")
    parser.add_argument("--contract-sha256")
    parser.add_argument("--document-sha256")
    args = parser.parse_args(argv)
    try:
        captured = {}
        for path in (args.contract, args.document):
            if path not in captured:
                captured[path] = engine.read_bytes(path)
        result = inspect(captured[args.contract], captured[args.document],
                         args.contract_sha256, args.document_sha256)
        encoded = json.dumps(result, ensure_ascii=True, indent=2).encode("utf-8")
        if len(encoded) > engine.MAX_BYTES:
            raise ValueError("complete output exceeds 1000000 bytes")
        print(encoded.decode("utf-8"))
        return 0 if result["valid"] else 1
    except (ValueError, OSError, RecursionError, InvalidOperation) as exc:
        print(json.dumps({"complete": False, "valid": False,
                          "error": str(exc)[:1000]}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
