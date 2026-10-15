#!/usr/bin/env python3
"""Replay a public-read batch against a separately retained exact-file hash."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import runpy
import sys

B = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'rpc-read-batch' / 'read_batch.py'))
PIN = re.compile(r'[0-9a-f]{64}\Z')


class PinError(ValueError):
    pass


def validate_pin(expected):
    if type(expected) is not str or not PIN.fullmatch(expected):
        raise PinError('expected SHA-256 must be 64 lowercase hex digits')


def review(raw, expected, require_results=False):
    """Pure offline check; never infer or update the expected pin from input."""
    validate_pin(expected)
    if type(raw) is not bytes or len(raw) > B['MAX_OUTPUT']:
        raise PinError('batch must be bytes, at most 99000 bytes')
    actual = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise PinError('file differs from the separately retained SHA-256')
    record = B['verify_record'](B['BASE']['parse_json'](raw))
    answers = {item['id']: item for item in record['responses']}
    calls = []
    for request in record['request']:
        response = answers[request['id']]
        outcome = 'error' if 'error' in response else 'result'
        calls.append({'id': request['id'], 'method': request['method'],
                      'params': request['params'], 'outcome': outcome,
                      outcome: response[outcome]})
    errors = sum(item['outcome'] == 'error' for item in calls)
    if require_results and errors:
        raise PinError(f'pin and replay match, but {errors} RPC call(s) returned errors')
    return {'status': 'retained_file_pin_and_batch_replay_match',
            'file_sha256': actual, 'file_bytes': len(raw),
            'captured_at_utc': record['captured_at_utc'],
            'rpc_url': record['rpc_url'], 'rpc_error_count': errors,
            'all_calls_returned_results': errors == 0, 'calls': calls,
            'limits': 'Exact retained bytes and internal replay only; no provider '
                      'authentication, state proof, freshness or result semantics. '
                      'The expected pin must be retained independently.'}


def verify(path, expected, require_results=False):
    validate_pin(expected)
    return review(B['SAFE']['read_bytes'](path, B['MAX_OUTPUT']),
                  expected, require_results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', help='visible relative workspace file')
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--require-results', action='store_true',
                        help='also reject well-formed RPC error responses')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify(args.record, args.expected_sha256,
                                args.require_results), indent=2, sort_keys=True))
        return 0
    except (ValueError, B['BASE']['SnapshotError'], OSError,
            TypeError, OverflowError, RecursionError) as exc:
        print('pinned-read-batch: ' + str(exc)[:1000], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
