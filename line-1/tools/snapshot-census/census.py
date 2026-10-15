#!/usr/bin/env python3
"""Inventory bounded RPC snapshots by exact request and observed answer."""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


CAPSULE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                             "snapshot-capsule" / "capsule.py"))
SAFE = CAPSULE["SAFE"]
MAX_SNAPSHOT = CAPSULE["MAX_SNAPSHOT"]
MAX_ITEMS = 32


def census(paths):
    """Read each file once, replay it offline, and group exact requests."""
    if not 1 <= len(paths) <= MAX_ITEMS:
        raise ValueError(f"choose between 1 and {MAX_ITEMS} snapshots")
    if len(set(paths)) != len(paths):
        raise ValueError("duplicate input path")
    groups = {}
    for path in sorted(paths):
        if len(path.encode("utf-8")) > 240:
            raise ValueError("input path exceeds 240 bytes")
        raw = SAFE["read_bytes"](path, MAX_SNAPSHOT)
        snapshot = CAPSULE["validate_snapshot"](raw)
        request = snapshot["request"]
        request_bytes = json.dumps(request, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True, allow_nan=False).encode("ascii")
        key = hashlib.sha256(request_bytes).hexdigest()
        if key not in groups:
            groups[key] = {"request_sha256": key, "method": request["method"],
                           "params": request["params"], "captures": []}
        groups[key]["captures"].append({
            "path": path,
            "bytes": len(raw),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "response_sha256": snapshot["response_sha256"],
            "captured_at_utc": snapshot["captured_at_utc"],
        })
    ordered = [groups[key] for key in sorted(groups)]
    for group in ordered:
        group["distinct_responses"] = len({capture["response_sha256"]
                                           for capture in group["captures"]})
    return {"schema": "line1-snapshot-census-v1", "count": len(paths),
            "request_groups": ordered}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", nargs="+", help="relative paths to bounded snapshot JSON files")
    args = parser.parse_args(argv)
    try:
        result = census(args.snapshots)
        print(json.dumps(result, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False))
        return 0
    except (ValueError, OSError, TypeError, OverflowError, RecursionError) as exc:
        print("snapshot-census: " + str(exc)[:1000], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
