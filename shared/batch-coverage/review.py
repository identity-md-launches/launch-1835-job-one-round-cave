#!/usr/bin/env python3
"""Review pinned RPC evidence and report exercised JSON contract branches."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
PIN = runpy.run_path(str(HERE / 'vendor/line-1/tools/pinned-read-batch/pin_batch.py'))
# Load the audit's own engine without depending on cwd or an ambient module name.
spec = importlib.util.spec_from_file_location(
    'batch_coverage_engine', HERE / 'vendor/line-2/tools/contract-path-audit/engine.py')
ENGINE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENGINE)
# audit.py imports 'engine'; isolate that one import and restore any prior module.
previous = sys.modules.get('engine')
sys.modules['engine'] = ENGINE
try:
    AUDIT = runpy.run_path(str(HERE / 'vendor/line-2/tools/contract-path-audit/audit.py'))
finally:
    if previous is None:
        del sys.modules['engine']
    else:
        sys.modules['engine'] = previous

LIMIT = 99_000
LIMITATIONS = ('Retained bytes, RPC replay and structural coverage only. Exercised does '
              'not mean all rules passed or all values were tested. A valid document may '
              'leave optional branches dormant. No provider authentication, current state, '
              'freshness, settlement, payment or signing authorization is established.')


def review(contract_raw, transcript_raw, contract_pin, transcript_pin,
           require_all_exercised=False):
    """Hash both captured sources before parsing either; never infer expected pins."""
    if type(require_all_exercised) is not bool:
        raise ValueError('require_all_exercised must be boolean')
    for role, raw, expected in (('contract', contract_raw, contract_pin),
                                ('transcript', transcript_raw, transcript_pin)):
        PIN['validate_pin'](expected)
        if type(raw) is not bytes or len(raw) > LIMIT:
            raise ValueError(role + ' must contain at most 99000 bytes')
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(role + ' SHA-256 mismatch')
    replay = PIN['review'](transcript_raw, transcript_pin)
    coverage = AUDIT['inspect'](contract_raw, transcript_raw, contract_pin, transcript_pin)
    counts = coverage['counts']
    all_exercised = counts['exercised'] == counts['declaredNodes']
    accepted = (replay['all_calls_returned_results'] and coverage['valid'] and
                (all_exercised or not require_all_exercised))
    state = ('rpc_error' if not replay['all_calls_returned_results'] else
             'contract_violation' if not coverage['valid'] else
             'coverage_required' if require_all_exercised and not all_exercised else
             'accepted')
    return {'accepted': accepted, 'complete': True, 'state': state,
            'requireAllExercised': require_all_exercised,
            'allDeclaredNodesExercised': all_exercised,
            'requestCount': len(replay['calls']),
            'rpcErrorCount': replay['rpc_error_count'],
            'coverage': coverage, 'limitations': LIMITATIONS}


def render(result):
    encoded = json.dumps(result, ensure_ascii=True, separators=(',', ':'), allow_nan=False) + '\n'
    if len(encoded.encode('ascii')) > LIMIT:
        raise ValueError('complete report exceeds 99000 bytes')
    return encoded


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('transcript')
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--transcript-sha256', required=True)
    parser.add_argument('--require-all-exercised', action='store_true')
    args = parser.parse_args(argv)
    try:
        # Refuse malformed expectations before any input read; capture each path once.
        PIN['validate_pin'](args.contract_sha256)
        PIN['validate_pin'](args.transcript_sha256)
        captured = {}
        for name in (args.contract, args.transcript):
            if name not in captured:
                captured[name] = ENGINE.read_bytes(name, LIMIT)
        result = review(captured[args.contract], captured[args.transcript],
                        args.contract_sha256, args.transcript_sha256,
                        args.require_all_exercised)
        sys.stdout.write(render(result))
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, TypeError, OverflowError, RecursionError,
            PIN['B']['BASE']['SnapshotError']) as exc:
        print(json.dumps({'accepted': False, 'complete': False, 'state': 'input_error',
                          'reason': str(exc)[:500]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
