"""Real retained ZTO replay plus adversarial integration cases; no network."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import review

HERE = Path(__file__).resolve().parent
CONTRACT = (HERE / 'zto-batch.contract.json').read_bytes()
TRANSCRIPT = (HERE / 'zto-batch.json').read_bytes()
CONTRACT_PIN = '38219d0c9192f3566be0bf9d650c8de7de0666b562f23f3b6be7bb2d01b3dae1'
TRANSCRIPT_PIN = 'b369c4f39db608ae240242db924f635a10dfb4e7b543a18113d3b110857c497a'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, separators=(',', ':')).encode()


def reseal(value):
    batch = review.PIN['B']
    value['request_sha256'] = batch['digest'](value['request'])
    value['responses_sha256'] = batch['digest'](value['responses'])
    value['transcript_sha256'] = batch['digest']({k: v for k, v in value.items()
                                               if k != 'transcript_sha256'})
    return encoded(value)


class CoverageReviewTests(unittest.TestCase):
    def check(self, contract=CONTRACT, transcript=TRANSCRIPT, **kwargs):
        # These hashes authorize only mutations within this test, not real evidence.
        return review.review(contract, transcript, sha(contract), sha(transcript), **kwargs)

    def test_real_zto_replay_without_transport(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            result = review.review(CONTRACT, TRANSCRIPT, CONTRACT_PIN, TRANSCRIPT_PIN, True)
        self.assertTrue(result['accepted'])
        self.assertTrue(result['allDeclaredNodesExercised'])
        self.assertEqual(result['requestCount'], 2)
        self.assertEqual(result['coverage']['counts']['violations'], 0)
        self.assertLess(len(review.render(result)), review.LIMIT)

    def test_both_pins_checked_before_parsing_either(self):
        with self.assertRaisesRegex(ValueError, 'transcript SHA-256 mismatch'):
            review.review(b'not json', b'changed', sha(b'not json'), TRANSCRIPT_PIN)
        with self.assertRaisesRegex(ValueError, 'contract SHA-256 mismatch'):
            review.review(b'changed', TRANSCRIPT, CONTRACT_PIN, TRANSCRIPT_PIN)

    def test_dormant_branch_requires_explicit_policy_to_decline(self):
        contract = json.loads(CONTRACT)
        contract['properties']['reviewNote'] = {'type': 'string'}
        raw = encoded(contract)
        result = self.check(contract=raw)
        self.assertTrue(result['accepted'])
        self.assertFalse(result['allDeclaredNodesExercised'])
        dormant = [n for n in result['coverage']['nodes'] if n['status'] == 'dormant']
        self.assertEqual([(n['contractPath'], n['reason']) for n in dormant],
                         [('/properties/reviewNote', 'property_absent')])
        strict = self.check(contract=raw, require_all_exercised=True)
        self.assertFalse(strict['accepted'])
        self.assertEqual(strict['state'], 'coverage_required')

    def test_resealed_imd_substitution_fails_structural_policy(self):
        value = json.loads(TRANSCRIPT)
        value['request'][0]['params'][0]['to'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        result = self.check(transcript=reseal(value))
        self.assertFalse(result['accepted'])
        self.assertEqual(result['state'], 'contract_violation')
        # All branches may be exercised while a rule still fails.
        self.assertTrue(result['allDeclaredNodesExercised'])

    def test_matching_pin_does_not_bypass_internal_checksums(self):
        value = json.loads(TRANSCRIPT)
        value['responses'][0]['result'] = '0x1'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.check(transcript=encoded(value))

    def test_rpc_error_never_accepted_by_permissive_contract(self):
        value = json.loads(TRANSCRIPT)
        value['responses'][0] = {'jsonrpc': '2.0', 'id': 1,
                                 'error': {'code': -32000, 'message': 'unavailable'}}
        result = self.check(contract=b'{"type":"object"}', transcript=reseal(value))
        self.assertTrue(result['coverage']['valid'])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['state'], 'rpc_error')

    def test_batch_reordering_works_with_order_independent_contract(self):
        value = json.loads(TRANSCRIPT)
        value['responses'].reverse()
        result = self.check(contract=b'{"type":"object"}', transcript=reseal(value))
        self.assertTrue(result['accepted'])
        # The example contract intentionally pins positional response order.
        self.assertEqual(self.check(transcript=reseal(value))['state'], 'contract_violation')

    def test_strict_json_and_source_bounds(self):
        for contract in (b'{"type":"object","type":"object"}', b'{"type":NaN}'):
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                self.check(contract=contract)
        with self.assertRaisesRegex(ValueError, '99000'):
            self.check(contract=b' ' * (review.LIMIT + 1))
        with self.assertRaises(ValueError):
            self.check(require_all_exercised=1)

    def test_provenance_pins_for_portable_copies(self):
        for row in json.loads((HERE / 'provenance.json').read_text()):
            relative = Path(row['copy']).relative_to('shared/batch-coverage')
            self.assertEqual(sha((HERE / relative).read_bytes()), row['sha256'])

    def test_no_follow_reader_refuses_external_paths(self):
        for path in ('/etc/passwd', '../escape', '.hidden', 'a//b'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                review.ENGINE.read_bytes(path, review.LIMIT)


if __name__ == '__main__':
    unittest.main()
