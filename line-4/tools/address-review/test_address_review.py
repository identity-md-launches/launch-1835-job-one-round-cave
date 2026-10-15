import copy
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import address_review as ar

HERE = Path(__file__).parent
ZTO = json.loads((HERE/'zto-payment.json').read_text())
POLICY = json.loads((HERE/'zto-expect.json').read_text())
PIN = '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'
IMD = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
# Published ERC-55 test vectors, fetched from ethereum/ercs ERCS/erc-55.md.
VECTORS = '''0x52908400098527886E0F7030069857D2E4169EE7
0x8617E340B3D01FA5F11F306F4090FD50E238070D
0xde709f2102306220921060314715629080e2fb77
0x27b1fdb04752bbc536007a920d24acb045561c26
0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed
0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359
0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB
0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb'''.splitlines()


class AddressReviewTests(unittest.TestCase):
    def test_published_checksum_vectors(self):
        for value in VECTORS:
            with self.subTest(value=value):
                self.assertEqual(ar.checksum_address(value.lower()), value)
                self.assertIsNot(ar.address_info(value)['mixedCaseChecksumValid'], False)

    def test_zto_pin_and_words(self):
        result = ar.review(ZTO, POLICY, PIN)
        self.assertTrue(result['checksPass'])
        self.assertEqual(len(result['addresses']), 2)
        self.assertEqual(result['addresses'][0]['word'], '0x'+('00'*12)+ZTO['message']['token'][2:])
        self.assertEqual(result['digest'], PIN)

    def test_invalid_case_does_not_change_digest(self):
        data = copy.deepcopy(ZTO)
        valid = ar.checksum_address(data['message']['token'])
        index = next(i for i,c in enumerate(valid[2:], 2) if c.isalpha())
        data['message']['token'] = valid[:index]+valid[index].swapcase()+valid[index+1:]
        result = ar.review(data, POLICY, PIN)
        self.assertFalse(result['checksPass'])
        self.assertEqual(result['invalidMixedCasePaths'], ['/message/token'])
        self.assertTrue(result['digestMatchesExpected'])
        self.assertTrue(result['addressesMatchExpected'])

    def test_uniform_case_unchecksummed(self):
        for value in (VECTORS[4].lower(), '0x'+VECTORS[4][2:].upper()):
            self.assertIsNone(ar.address_info(value)['mixedCaseChecksumValid'])

    def test_wrong_token_and_digest(self):
        data = copy.deepcopy(ZTO); data['message']['token'] = IMD
        result = ar.review(data, POLICY, PIN)
        self.assertEqual(result['changedAddresses'], ['/message/token'])
        self.assertFalse(result['digestMatchesExpected'])
        self.assertFalse(result['checksPass'])

    def test_address_only_policy_does_not_pin_amount(self):
        data = copy.deepcopy(ZTO)
        data['message']['minimumRaw'] = str(int(data['message']['minimumRaw'])+1)
        self.assertTrue(ar.review(data, POLICY)['checksPass'])
        pinned = ar.review(data, POLICY, PIN)
        self.assertTrue(pinned['addressesMatchExpected'])
        self.assertFalse(pinned['checksPass'])
        self.assertFalse(pinned['digestMatchesExpected'])

    def test_expectations_require_exact_path_set(self):
        policy = copy.deepcopy(POLICY)
        del policy['addresses']['/message/token']
        policy['addresses']['/message/absent'] = IMD
        result = ar.review(ZTO, policy)
        self.assertEqual(result['missingAddresses'], ['/message/absent'])
        self.assertEqual(result['unexpectedAddresses'], ['/message/token'])
        self.assertFalse(result['checksPass'])

    def test_case_equivalence_policy(self):
        policy = copy.deepcopy(POLICY)
        policy['addresses'] = {p: ar.checksum_address(v) for p,v in policy['addresses'].items()}
        self.assertTrue(ar.review(ZTO, policy)['checksPass'])

    def test_nested_arrays_domain_and_recursive_types(self):
        data = {'types': {'EIP712Domain':[{'name':'verifyingContract','type':'address'}],
                'Node':[{'name':'who','type':'address'}, {'name':'children','type':'Node[]'}],
                'Root':[{'name':'nodes','type':'Node[][1]'}, {'name':'ignored','type':'string'}]},
                'primaryType':'Root', 'domain':{'verifyingContract':IMD},
                'message':{'nodes':[[{'who': ZTO['message']['token'], 'children':[
                    {'who':ZTO['message']['recipient'],'children':[]}]}]], 'ignored': IMD}}
        paths = [r['path'] for r in ar.review(data)['addresses']]
        self.assertEqual(paths, ['/domain/verifyingContract','/message/nodes/0/0/who',
                                '/message/nodes/0/0/children/0/who'])

    def test_no_addresses_unused_type(self):
        data = copy.deepcopy(ZTO)
        data['types']['PaymentEvidence'] = []
        data['types']['Unused'] = [{'name':'who','type':'address'}]
        data['message'] = {}
        self.assertEqual(ar.review(data, {'addresses':{}})['addresses'], [])

    def test_no_mutation_and_no_pins(self):
        data, policy = copy.deepcopy(ZTO), copy.deepcopy(POLICY)
        ar.review(data, policy)
        self.assertEqual(data, ZTO); self.assertEqual(policy, POLICY)
        result = ar.review(data)
        self.assertFalse(result['addressExpectationProvided'])
        self.assertFalse(result['digestExpectationProvided'])

    def test_invalid_policies(self):
        for policy in ({}, {'addresses':[]}, {'addresses':{'/message/00':IMD}},
                       {'addresses':{'/message/token':'bad'}}, {'addresses':{},'extra':1}):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                ar.review(ZTO, policy)
        bad = VECTORS[4].replace('5aA', '5AA')
        with self.assertRaises(ValueError):
            ar.review(ZTO, {'addresses':{'/message/token':bad}})

    def test_invalid_typed_data_and_bounds(self):
        data = copy.deepcopy(ZTO); data['message']['token'] = '0x1234'
        with self.assertRaises(ValueError): ar.review(data)
        with patch.object(ar, 'MAX_ADDRESSES', 1), self.assertRaises(ValueError): ar.review(ZTO)
        with patch.object(ar, 'MAX_REPORT_BYTES', 20), self.assertRaises(ValueError): ar.review(ZTO)
        with self.assertRaises(ValueError): ar.review(ZTO, expected_digest='bad')

    def test_cli_statuses_and_atomic_output(self):
        fixture = str(HERE/'zto-payment.json'); policy = str(HERE/'zto-expect.json')
        for args, code in (([fixture,'--expect-addresses',policy,'--digest-expect',PIN],0),
                           ([fixture,'--digest-expect', '0x'+'ab'*32],1),
                           ([fixture,'--expect-addresses','../forbidden.json'],2),
                           ([fixture,'--digest-expect','bad'],2)):
            stdout,stderr=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                actual=ar.main(args)
            self.assertEqual(actual,code)
            if code==2:
                self.assertEqual(stdout.getvalue(),''); self.assertTrue(stderr.getvalue())
            else:
                self.assertEqual(json.loads(stdout.getvalue())['checksPass'], code==0)

    def test_null_policy_cli_rejected(self):
        with patch.object(ar,'load_workspace_json',side_effect=[ZTO,None]):
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ar.main(['input','--expect-addresses','policy']),2)
            self.assertEqual(out.getvalue(),'')


if __name__ == '__main__': unittest.main()
