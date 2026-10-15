#!/usr/bin/env python3
"""Capture and replay a bounded batch of public Ethereum JSON-RPC reads."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import runpy
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parents[1]
BASE = runpy.run_path(str(HERE / "bounded-rpc-snapshot" / "snapshot.py"))
SAFE = runpy.run_path(str(HERE / "safe-snapshot-files" / "safe_files.py"))
SCHEMA = "line1-rpc-read-batch-v1"
ENDPOINTS = {"ethereum-rpc.publicnode.com", "eth.drpc.org"}
MAX_ITEMS = 12
MAX_PLAN = 16_384
MAX_RESPONSE = 65_536
MAX_OUTPUT = 99_000


class BatchError(ValueError):
    """Invalid plan, response, or portable read record."""


def require(ok, message):
    if not ok:
        raise BatchError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_endpoint(url):
    require(type(url) is str, "RPC URL must be text")
    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise BatchError("invalid RPC URL") from exc
    require(parts.scheme == "https" and parts.hostname in ENDPOINTS and
            parts.username is None and parts.password is None and
            port in (None, 443) and parts.path in ("", "/") and
            not parts.query and not parts.fragment,
            "use one of the documented public HTTPS RPC endpoints without credentials")
    return url


def validate_requests(requests):
    require(type(requests) is list and 1 <= len(requests) <= MAX_ITEMS,
            f"batch must contain 1 to {MAX_ITEMS} requests")
    result = []
    for index, item in enumerate(requests, 1):
        require(type(item) is dict and set(item) == {"method", "params"},
                "each plan entry must contain only method and params")
        method, params = item["method"], item["params"]
        try:
            BASE["validate_request"](method, params)
        except BASE["SnapshotError"] as exc:
            raise BatchError(str(exc)) from exc
        result.append({"jsonrpc": "2.0", "id": index,
                       "method": method, "params": params})
    return result


def validate_answers(requests, responses):
    require(type(responses) is list and len(responses) == len(requests),
            "response batch length does not match request batch")
    wanted = {entry["id"]: entry for entry in requests}
    seen = set()
    clean = []
    for response in responses:
        require(type(response) is dict and response.get("jsonrpc") == "2.0" and
                type(response.get("id")) is int and response["id"] in wanted,
                "response version or request ID mismatch")
        rid = response["id"]
        require(rid not in seen, "duplicate response ID")
        seen.add(rid)
        require(("result" in response) != ("error" in response),
                "response needs exactly one of result or error")
        if "error" in response:
            error = response["error"]
            require(type(error) is dict and type(error.get("code")) is int and
                    type(error.get("message")) is str,
                    "malformed JSON-RPC error response")
        clean.append(response)
    require(seen == set(wanted), "one or more request IDs have no response")
    return clean


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise BatchError("RPC endpoint redirected; refusing another destination")


def capture(url, requests, timeout):
    validate_endpoint(url)
    batch = validate_requests(requests)
    body = json.dumps(batch, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
    require(len(body) <= MAX_PLAN, "encoded request batch exceeds byte limit")
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "identity", "User-Agent": "IdentityMD-Line1-RPCBatch/1.0",
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            require(response.status == 200, f"HTTP {response.status}")
            raw = response.read(MAX_RESPONSE + 1)
            require(len(raw) <= MAX_RESPONSE, "RPC response batch exceeds byte limit")
            content_type = response.headers.get("Content-Type", "")
    except BatchError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BatchError(f"RPC transport failed: {exc}") from exc
    try:
        answers = BASE["parse_json"](raw)
    except BASE["SnapshotError"] as exc:
        raise BatchError(str(exc)) from exc
    validate_answers(batch, answers)
    record = {
        "schema": SCHEMA,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "rpc_url": url,
        "http_status": 200,
        "content_type": content_type[:256],
        "request": batch,
        "responses": answers,
        "request_sha256": digest(batch),
        "responses_sha256": digest(answers),
    }
    record["transcript_sha256"] = digest(record)
    rendered = (json.dumps(record, indent=2, sort_keys=True,
                            ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    require(len(rendered) <= MAX_OUTPUT, "portable batch record exceeds output limit")
    return record, rendered


def verify_record(value):
    required = {"schema", "captured_at_utc", "rpc_url", "http_status",
                "content_type", "request", "responses", "request_sha256",
                "responses_sha256", "transcript_sha256"}
    require(type(value) is dict and set(value) == required,
            "record fields do not match the supported schema")
    require(value["schema"] == SCHEMA, "unsupported batch record schema")
    validate_endpoint(value["rpc_url"])
    require(type(value["http_status"]) is int and value["http_status"] == 200 and
            type(value["content_type"]) is str and len(value["content_type"]) <= 256,
            "invalid HTTP metadata")
    captured = value["captured_at_utc"]
    require(type(captured) is str, "capture time must be text")
    try:
        moment = datetime.fromisoformat(captured)
    except ValueError as exc:
        raise BatchError("invalid capture time") from exc
    require(moment.tzinfo is not None and moment.utcoffset().total_seconds() == 0,
            "capture time must include UTC offset")
    requests = value["request"]
    require(type(requests) is list and 1 <= len(requests) <= MAX_ITEMS,
            "invalid stored request batch")
    for index, entry in enumerate(requests, 1):
        require(type(entry) is dict and set(entry) == {
            "jsonrpc", "id", "method", "params"} and
            entry["jsonrpc"] == "2.0" and type(entry["id"]) is int and
            entry["id"] == index, "invalid stored request envelope")
        try:
            BASE["validate_request"](entry["method"], entry["params"])
        except BASE["SnapshotError"] as exc:
            raise BatchError(str(exc)) from exc
    responses = validate_answers(requests, value["responses"])
    require(value["request_sha256"] == digest(requests),
            "request batch checksum mismatch")
    require(value["responses_sha256"] == digest(responses),
            "response batch checksum mismatch")
    unsigned = {key: item for key, item in value.items()
                if key != "transcript_sha256"}
    require(value["transcript_sha256"] == digest(unsigned),
            "transcript checksum mismatch")
    return value


def load_json(path, limit):
    try:
        raw = SAFE["read_bytes"](path, limit)
        return BASE["parse_json"](raw)
    except (SAFE["FileBoundaryError"], BASE["SnapshotError"], OSError) as exc:
        raise BatchError(str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    grab = commands.add_parser("capture", help="send a bounded public-read batch")
    grab.add_argument("--plan", required=True, help="workspace JSON plan")
    grab.add_argument("--rpc-url", default="https://ethereum-rpc.publicnode.com")
    grab.add_argument("--output", required=True, help="new workspace JSON path")
    grab.add_argument("--timeout", type=float, default=15.0)
    review = commands.add_parser("verify", help="replay-check a saved batch offline")
    review.add_argument("record")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            require(0 < args.timeout <= 60, "timeout must be between 0 and 60 seconds")
            plan = load_json(args.plan, MAX_PLAN)
            require(type(plan) is dict and set(plan) == {"requests"},
                    "plan must contain only a requests array")
            batch = validate_requests(plan["requests"])
            # Remove generated RPC envelope fields; capture assigns stable IDs itself.
            requests = [{"method": entry["method"], "params": entry["params"]}
                        for entry in batch]
            record, rendered = capture(args.rpc_url, requests, args.timeout)
            SAFE["write_bytes"](args.output, rendered, MAX_OUTPUT)
            summary = verify_record(record)
            print(json.dumps({"accepted": True, "count": len(summary["request"]),
                              "transcript_sha256": summary["transcript_sha256"],
                              "output": args.output}, separators=(",", ":")))
        else:
            record = verify_record(load_json(args.record, MAX_OUTPUT))
            calls = []
            answer_by_id = {answer["id"]: answer for answer in record["responses"]}
            for request in record["request"]:
                answer = answer_by_id[request["id"]]
                calls.append({"id": request["id"], "method": request["method"],
                              "outcome": "error" if "error" in answer else "result"})
            print(json.dumps({"accepted": True, "count": len(calls),
                              "calls": calls,
                              "transcript_sha256": record["transcript_sha256"]},
                             separators=(",", ":")))
        return 0
    except (BatchError, SAFE["FileBoundaryError"], OSError, ValueError,
            TypeError, OverflowError, RecursionError) as exc:
        print("rpc-read-batch: " + str(exc)[:1000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
