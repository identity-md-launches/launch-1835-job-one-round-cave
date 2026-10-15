#!/usr/bin/env python3
"""Offline EIP-712 schema recursion and finite-value feasibility review."""
import argparse
import json
import sys
from typed_digest import ARRAY, Encoder, TypedDataError, base_type, load_workspace_json, validate_tree


def cyclic_components(edges):
    """Small bounded graph: mutual reachability partitions strongly connected sets."""
    reachable = {}
    for root in edges:
        seen, pending = set(), list(edges[root])
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(edges[node])
        reachable[root] = seen
    remaining, result = set(edges), []
    for root in sorted(edges):
        if root not in remaining:
            continue
        component = sorted(n for n in remaining
                           if n == root or (n in reachable[root] and root in reachable[n]))
        remaining.difference_update(component)
        if len(component) > 1 or root in edges[root]:
            result.append(component)
    return result


def review(schema):
    validate_tree(schema)
    if not isinstance(schema, dict) or set(schema) != {'types', 'primaryType'}:
        raise TypedDataError('schema needs exactly types and primaryType')
    types = Encoder(schema['types']).types
    primary = schema['primaryType']
    if not isinstance(primary, str) or primary not in types or primary == 'EIP712Domain':
        raise TypedDataError('primaryType must name a message struct')
    all_edges = {n: set() for n in types}
    required_edges = {n: set() for n in types}
    fields = []
    for name in sorted(types):
        for field in types[name]:
            target = base_type(field['type'])
            if target not in types:
                continue
            kind, can_empty = field['type'], False
            while (match := ARRAY.fullmatch(kind)):
                can_empty |= match.group(2) == ''
                kind = match.group(1)
            all_edges[name].add(target)
            if not can_empty:
                required_edges[name].add(target)
            fields.append({'from': name, 'field': field['name'], 'to': target,
                           'declaredType': field['type'], 'canCutWithEmptyArray': can_empty})
    # A required reference to an impossible struct also makes its owner impossible.
    impossible = {n for group in cyclic_components(required_edges) for n in group}
    while True:
        expanded = impossible | {n for n, children in required_edges.items() if children & impossible}
        if expanded == impossible:
            break
        impossible = expanded
    roots = ['EIP712Domain', primary]
    return {'primaryType': primary, 'recursiveComponents': cyclic_components(all_edges),
            'requiredCycles': cyclic_components(required_edges),
            'typesWithoutFiniteValues': sorted(impossible),
            'rootsHaveFiniteValues': not any(n in impossible for n in roots),
            'references': fields,
            'interpretation': 'Schema-only feasibility: dynamic arrays can terminate with []. '
            'Fixed arrays and direct struct fields require child values. Recursion is not '
            'itself invalid. This does not validate message values, calculate a digest, '
            'check wallet support, or authorize signing.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schema')
    parser.add_argument('--require-finite', action='store_true',
                        help='exit 1 when domain or message cannot have finite values')
    args = parser.parse_args()
    try:
        result = review(load_workspace_json(args.schema))
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return int(args.require_finite and not result['rootsHaveFiniteValues'])
    except (TypedDataError, OSError, ValueError, RecursionError) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
