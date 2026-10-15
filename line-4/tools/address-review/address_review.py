#!/usr/bin/env python3
"""Inspect reachable EIP-712 addresses and explicit address expectations offline."""
import argparse
import json
import re
import sys
from typed_digest import ARRAY, Encoder, TypedDataError, digest, keccak256, load_workspace_json, parse_hex, validate_tree

MAX_ADDRESSES = 128
MAX_REPORT_BYTES = 100_000
PATH = re.compile(r'^/(domain|message)(/([A-Za-z_][A-Za-z0-9_]*|0|[1-9][0-9]*))+$')


def checksum_address(value):
    """EIP-55 uses Keccak of lowercase ASCII hex, WITHOUT the 0x prefix."""
    raw = parse_hex(value, 20).hex()
    hashed = keccak256(raw.encode('ascii')).hex()
    return '0x' + ''.join(c.upper() if c in 'abcdef' and int(h, 16) >= 8 else c
                          for c, h in zip(raw, hashed))


def address_info(value):
    raw = parse_hex(value, 20)
    canonical = checksum_address(value)
    body = value[2:]
    letters = ''.join(c for c in body if c.lower() in 'abcdef')
    mixed = bool(letters) and letters != letters.lower() and letters != letters.upper()
    return {'input': value, 'address': '0x'+raw.hex(), 'checksumAddress': canonical,
            'spelling': 'mixed' if mixed else 'upper' if letters and letters == letters.upper() else 'lower',
            'mixedCaseChecksumValid': body == canonical[2:] if mixed else None,
            'isZero': not any(raw), 'word': '0x'+raw.rjust(32, b'\0').hex()}


def render(report):
    text = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    if len(text.encode('ascii')) > MAX_REPORT_BYTES:
        raise TypedDataError('address report exceeds 100000 bytes')
    return text


def expectations(policy):
    validate_tree(policy)
    if not isinstance(policy, dict) or set(policy) != {'addresses'} or not isinstance(policy['addresses'], dict):
        raise TypedDataError('expectations need exactly an addresses object')
    if len(policy['addresses']) > MAX_ADDRESSES:
        raise TypedDataError('too many expected addresses')
    wanted = {}
    for path, value in policy['addresses'].items():
        if not PATH.fullmatch(path):
            raise TypedDataError('expected path must be a canonical address JSON Pointer')
        info = address_info(value)
        if info['mixedCaseChecksumValid'] is False:
            raise TypedDataError('invalid mixed-case checksum in expectation at '+path)
        wanted[path] = info['address']
    return wanted


def review(data, policy=None, expected_digest=None):
    hashes = digest(data)  # Complete input validation before collecting fields.
    encoder = Encoder(data['types'])
    wanted = expectations(policy) if policy is not None else None
    pin = parse_hex(expected_digest, 32).hex() if expected_digest is not None else None
    rows = []

    def visit(kind, value, path):
        array = ARRAY.fullmatch(kind)
        if array:
            for i, item in enumerate(value):
                visit(array.group(1), item, path+'/'+str(i))
        elif kind in encoder.types:
            for field in encoder.types[kind]:
                visit(field['type'], value[field['name']], path+'/'+field['name'])
        elif kind == 'address':
            if len(rows) >= MAX_ADDRESSES:
                raise TypedDataError('review exceeds 128 addresses')
            rows.append({'path': path, **address_info(value)})

    visit('EIP712Domain', data['domain'], '/domain')
    visit(data['primaryType'], data['message'], '/message')
    invalid = [r['path'] for r in rows if r['mixedCaseChecksumValid'] is False]
    report = {'reviewVersion': 1, **hashes, 'addresses': rows,
              'invalidMixedCasePaths': invalid,
              'zeroAddressPaths': [r['path'] for r in rows if r['isZero']],
              'addressExpectationProvided': wanted is not None,
              'digestExpectationProvided': pin is not None}
    if wanted is not None:
        actual = {r['path']: r['address'] for r in rows}
        report.update(missingAddresses=sorted(wanted.keys()-actual.keys()),
                      unexpectedAddresses=sorted(actual.keys()-wanted.keys()),
                      changedAddresses=sorted(p for p in actual.keys() & wanted.keys() if actual[p] != wanted[p]),
                      addressesMatchExpected=actual == wanted)
    if pin is not None:
        report['digestMatchesExpected'] = hashes['digest'][2:] == pin
    report['checksPass'] = not invalid and report.get('addressesMatchExpected', True) and report.get('digestMatchesExpected', True)
    report['interpretation'] = ('Address bytes determine the digest regardless of letter case. '
        'Mixed-case spellings are checked against chain-independent EIP-55; all-lower and all-upper '
        'spellings are unchecksummed. Zero addresses are reported, not rejected. Address expectations '
        'pin every reachable address path, not non-address fields, schema or signer identity. '
        'No result proves ownership, contract support, payment, consent or replay safety.')
    render(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--expect-addresses')
    parser.add_argument('--digest-expect')
    args = parser.parse_args(argv)
    try:
        data = load_workspace_json(args.input)
        policy = load_workspace_json(args.expect_addresses) if args.expect_addresses is not None else None
        if args.expect_addresses is not None and policy is None:
            raise TypedDataError('expectations cannot be null')
        report = review(data, policy, args.digest_expect)
        print(render(report), end='')
        return 0 if report['checksPass'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print('address-review: '+json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
