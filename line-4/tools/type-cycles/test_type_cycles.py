import copy
import unittest
from type_cycles import review
from typed_digest import TypedDataError


def schema(types, root='A'):
    return {'primaryType': root, 'types': {'EIP712Domain': [], **types}}


def field(kind):
    return {'name': 'child', 'type': kind}


class CycleTests(unittest.TestCase):
    def test_dynamic_self_recursion_terminates(self):
        r = review(schema({'A': [field('A[]')]}))
        self.assertEqual(r['recursiveComponents'], [['A']])
        self.assertEqual(r['requiredCycles'], [])
        self.assertTrue(r['rootsHaveFiniteValues'])

    def test_required_mutual_cycle_and_parent(self):
        r = review(schema({'A': [field('B')], 'B': [field('C[2]')],
                           'C': [field('B')]}))
        self.assertEqual(r['requiredCycles'], [['B', 'C']])
        self.assertEqual(r['typesWithoutFiniteValues'], ['A', 'B', 'C'])
        self.assertFalse(r['rootsHaveFiniteValues'])

    def test_dynamic_parent_of_impossible_type_can_be_empty(self):
        r = review(schema({'A': [field('B[][2]')], 'B': [field('B')]}))
        self.assertEqual(r['typesWithoutFiniteValues'], ['B'])
        self.assertTrue(r['rootsHaveFiniteValues'])

    def test_cycle_cut_by_dynamic_edge(self):
        r = review(schema({'A': [field('B')], 'B': [field('A[]')]}))
        self.assertEqual(r['recursiveComponents'], [['A', 'B']])
        self.assertTrue(r['rootsHaveFiniteValues'])

    def test_independent_components_and_order(self):
        r = review(schema({'A': [field('A')], 'B': [field('C')], 'C': [field('B')]}))
        self.assertEqual(r['requiredCycles'], [['A'], ['B', 'C']])

    def test_acyclic_diamond(self):
        r = review(schema({'A': [field('B'), {'name': 'other', 'type': 'C'}],
                           'B': [field('D')], 'C': [field('D')], 'D': []}))
        self.assertEqual(r['recursiveComponents'], [])
        self.assertTrue(r['rootsHaveFiniteValues'])

    def test_domain_is_also_a_root(self):
        s = schema({'A': []})
        s['types']['EIP712Domain'] = [field('EIP712Domain')]
        self.assertFalse(review(s)['rootsHaveFiniteValues'])

    def test_input_unchanged(self):
        s = schema({'A': [field('A[]')]})
        before = copy.deepcopy(s)
        review(s)
        self.assertEqual(s, before)

    def test_unknown_reference_and_zero_array_reject(self):
        for kind in ['Missing', 'A[0]']:
            with self.assertRaises(TypedDataError):
                review(schema({'A': [field(kind)]}))

    def test_extra_keys_and_bad_root_reject(self):
        for s in [dict(schema({'A': []}), message={}), schema({'A': []}, 'Missing')]:
            with self.assertRaises(TypedDataError):
                review(s)


if __name__ == '__main__':
    unittest.main()
