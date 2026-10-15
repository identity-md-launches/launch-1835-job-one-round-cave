import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

P = runpy.run_path(str(Path(__file__).with_name('pin_batch.py')))
B = P['B']
SOURCE = Path('line-1/tools/rpc-read-batch/live-zto-batch.json')
EXPECTED = 'b369c4f39db608ae240242db924f635a10dfb4e7b543a18113d3b110857c497a'


def reseal(record):
    record['request_sha256'] = B['digest'](record['request'])
    record['responses_sha256'] = B['digest'](record['responses'])
    record['transcript_sha256'] = B['digest']({
        k: v for k, v in record.items() if k != 'transcript_sha256'})
    return json.dumps(record).encode()


class PinBatchTests(unittest.TestCase):
    def setUp(self):
        self.raw = SOURCE.read_bytes()
        self.record = json.loads(self.raw)

    def test_real_zto_offline(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            result = P['verify'](str(SOURCE), EXPECTED, True)
        self.assertEqual(result['rpc_error_count'], 0)
        self.assertEqual([int(c['result'], 16) for c in result['calls']],
                         [10**27, 18])
        self.assertEqual(SOURCE.read_bytes(), self.raw)

    def test_resealed_replacement(self):
        altered = copy.deepcopy(self.record)
        altered['responses'][0]['result'] = '0x1'
        raw = reseal(altered)
        B['verify_record'](json.loads(raw))
        with self.assertRaisesRegex(P['PinError'], 'differs'):
            P['review'](raw, EXPECTED)
        # Replacing the independently expected pin defeats replacement detection.
        self.assertEqual(P['review'](raw, hashlib.sha256(raw).hexdigest())
                         ['calls'][0]['result'], '0x1')

    def test_whitespace_is_pinned(self):
        with self.assertRaises(P['PinError']):
            P['review'](self.raw + b' ', EXPECTED)

    def test_bad_pin_before_read(self):
        for pin in ('', '0'*63, EXPECTED.upper(), 42, 'g'*64):
            with self.subTest(pin=pin), patch.dict(B['SAFE'], {
                    'read_bytes': lambda *a: self.fail('read before valid pin')}):
                with self.assertRaises(P['PinError']):
                    P['verify']('not-present', pin)

    def test_matching_pin_still_checks_replay(self):
        self.record['responses'][0]['result'] = '0x1'
        raw = json.dumps(self.record).encode()
        with self.assertRaisesRegex(B['BatchError'], 'checksum'):
            P['review'](raw, hashlib.sha256(raw).hexdigest())

    def test_error_is_explicit(self):
        self.record['responses'][0] = {'id': 1, 'jsonrpc': '2.0',
            'error': {'code': -32000, 'message': 'unavailable'}}
        raw = reseal(self.record)
        pin = hashlib.sha256(raw).hexdigest()
        result = P['review'](raw, pin)
        self.assertFalse(result['all_calls_returned_results'])
        self.assertEqual(result['rpc_error_count'], 1)
        with self.assertRaisesRegex(P['PinError'], 'returned errors'):
            P['review'](raw, pin, True)

    def test_response_order_correlated_by_id(self):
        self.record['responses'].reverse()
        raw = reseal(self.record)
        result = P['review'](raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual([c['id'] for c in result['calls']], [1, 2])
        self.assertEqual(int(result['calls'][1]['result'], 16), 18)

    def test_strict_json_and_byte_limit(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises(B['BASE']['SnapshotError']):
                P['review'](raw, hashlib.sha256(raw).hexdigest())
        with self.assertRaisesRegex(P['PinError'], '99000'):
            P['review'](b'x'*99001, EXPECTED)

    def test_boundary(self):
        for path in ('/etc/passwd', '../outside', '.hidden', 'line-1/../GOAL.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                P['verify'](path, EXPECTED)


if __name__ == '__main__':
    unittest.main()
