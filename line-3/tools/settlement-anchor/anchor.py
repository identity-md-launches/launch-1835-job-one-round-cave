#!/usr/bin/env python3
"""Bind a successful settlement verdict to its recorded canonical slot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_BYTES = 100_000
HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")


class AnchorError(ValueError):
    pass


def strict_json(raw):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise AnchorError("bounded UTF-8 JSON required")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AnchorError("duplicate JSON key")
            out[key] = value
        return out

    def constant(value):
        raise AnchorError("nonfinite JSON value")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise AnchorError("invalid JSON") from exc


def hash32(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise AnchorError("expected 32-byte hash")
    return value.lower()


def uint(value, label, maximum=2**64 - 1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise AnchorError(label + " must be an unsigned integer")
    return value


def anchor(bundle):
    """Accept only when policy, settlement and position describe one slot."""
    if not isinstance(bundle, dict) or set(bundle) != {"policy", "settlement", "position"}:
        raise AnchorError("exact policy, settlement and position fields required")
    policy = bundle["policy"]
    if (not isinstance(policy, dict) or set(policy) !=
            {"transactionHash", "minimumConfirmations", "requireFinalized"}):
        raise AnchorError("exact policy fields required")
    tx = hash32(policy["transactionHash"])
    minimum = uint(policy["minimumConfirmations"], "minimum confirmations", 2**32 - 1)
    if minimum < 1 or type(policy["requireFinalized"]) is not bool:
        raise AnchorError("invalid settlement policy")

    settlement = bundle["settlement"]
    if (not isinstance(settlement, dict) or set(settlement) !=
            {"settled", "transactionHash", "execution", "inclusion", "head",
             "confirmations", "finalized"}):
        raise AnchorError("exact settlement verdict required")
    if settlement["settled"] is not True or settlement["execution"] != "succeeded":
        return {"anchored": False, "state": "settlement_not_accepted",
                "evidenceChecked": True}
    if hash32(settlement["transactionHash"]) != tx:
        raise AnchorError("settlement transaction differs from policy")
    inclusion = settlement["inclusion"]
    head = settlement["head"]
    if (not isinstance(inclusion, dict) or set(inclusion) != {"number", "hash"}
            or not isinstance(head, dict) or set(head) != {"number", "hash"}):
        raise AnchorError("exact settlement block anchors required")
    inclusion_number = uint(inclusion["number"], "inclusion block")
    inclusion_hash = hash32(inclusion["hash"])
    head_number, head_hash = uint(head["number"], "head block"), hash32(head["hash"])
    confirmations = uint(settlement["confirmations"], "confirmations")
    if confirmations != head_number - inclusion_number + 1 or confirmations < minimum:
        return {"anchored": False, "state": "confirmation_policy_failed",
                "evidenceChecked": True}
    finalized = settlement["finalized"]
    if type(finalized) is not bool:
        raise AnchorError("finalized must be boolean")
    if policy["requireFinalized"] and finalized is not True:
        return {"anchored": False, "state": "finality_policy_failed",
                "evidenceChecked": True}

    position = bundle["position"]
    if (not isinstance(position, dict) or set(position) !=
            {"transactionHash", "block", "transactionIndex", "transactionCount"}):
        raise AnchorError("exact position fields required")
    if hash32(position["transactionHash"]) != tx:
        raise AnchorError("position transaction differs from policy")
    block = position["block"]
    if not isinstance(block, dict) or set(block) != {"number", "hash"}:
        raise AnchorError("exact position block anchor required")
    block_number, block_hash = uint(block["number"], "position block"), hash32(block["hash"])
    index = uint(position["transactionIndex"], "transaction index", 2**32 - 1)
    count = uint(position["transactionCount"], "transaction count", 2**32 - 1)
    if count < 1 or index >= count:
        raise AnchorError("transaction index outside block")
    if (block_number, block_hash) != (inclusion_number, inclusion_hash):
        return {"anchored": False, "state": "block_anchor_mismatch",
                "evidenceChecked": True}
    if head_number < inclusion_number:
        raise AnchorError("head precedes inclusion")
    return {"anchored": True, "state": "settlement_slot_anchored",
            "transactionHash": tx, "block": {"number": block_number, "hash": block_hash},
            "transactionIndex": index, "transactionCount": count,
            "head": {"number": head_number, "hash": head_hash},
            "confirmations": confirmations, "finalized": finalized,
            "evidenceChecked": True,
            "limitations": "This joins retained provider assertions; it is not a consensus or trie proof, and a later reorg remains possible."}


def load(path):
    if (not isinstance(path, str) or not path or path.startswith("/") or "\\" in path
            or any(not part or part.startswith(".") for part in path.split("/"))):
        raise AnchorError("visible workspace-relative bundle path required")
    if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY") or
            os.open not in os.supports_dir_fd):
        raise AnchorError("safe bundle file opens unsupported on this platform")
    directory = descriptor = None
    try:
        directory = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
        parts = path.split("/")
        for part in parts[:-1]:
            next_directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                     dir_fd=directory)
            os.close(directory)
            directory = next_directory
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise AnchorError("bundle must be a regular file inside the workspace")
        chunks, size = [], 0
        while size <= MAX_BYTES:
            chunk = os.read(descriptor, min(8192, MAX_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        if size > MAX_BYTES:
            raise AnchorError("bundle exceeds 100 KB")
        return b"".join(chunks)
    except OSError:
        raise AnchorError("bundle could not be opened safely") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory is not None:
            os.close(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true")
    source.add_argument("--bundle")
    args = parser.parse_args(argv)
    try:
        if args.demo:
            path = (Path(__file__).resolve().parent / "demo-anchor.json").relative_to(Path.cwd())
        else:
            path = args.bundle
        raw = load(str(path))
        result = anchor(strict_json(raw))
        result["bundleSha256"] = hashlib.sha256(raw).hexdigest()
        if args.demo:
            result["demoNote"] = "Retained real ZTO settlement and position; historical offline example."
        encoded = json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        if len(encoded.encode("ascii")) > MAX_BYTES:
            raise AnchorError("output exceeds size limit")
        print(encoded, end="")
        return 0 if result["anchored"] else 1
    except (AnchorError, OSError, TypeError, ValueError, RecursionError):
        print(json.dumps({"anchored": False, "state": "input_error"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
