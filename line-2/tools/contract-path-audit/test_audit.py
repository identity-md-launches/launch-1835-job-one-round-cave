#!/usr/bin/env python3
"""Focused regression tests for branch coverage and inherited validation."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

import audit


HERE = Path(__file__).parent
ROOT = HERE.parents[2]


class ContractPathAuditTests(unittest.TestCase):
    def test_optional_and_required_absence(self):
        contract = {"type": "object", "required": ["need"], "properties": {
            "need": {"type": "integer"},
            "optional/field": {"type": "object", "properties": {
                "nested~field": {"type": "string"}}}}}
        result = audit.audit(contract, {})
        nodes = {n["contractPath"]: n for n in result["nodes"]}
        self.assertEqual(result["counts"], {
            "declaredNodes": 4, "exercised": 1, "typeRejected": 0,
            "dormant": 3, "violations": 1})
        self.assertEqual(nodes["/properties/need"]["reason"], "property_absent")
        self.assertEqual(nodes["/properties/optional~1field"]["reason"], "property_absent")
        self.assertEqual(nodes["/properties/optional~1field/properties/nested~0field"]["reason"],
                         "parent_dormant")
        self.assertEqual(result["errors"][0]["path"], "/need")

    def test_parent_type_rejection_prevents_child_visit(self):
        result = audit.audit({"type": "object", "properties": {
            "x": {"type": "array", "items": {"type": "string"}}}}, {"x": 3})
        nodes = {n["contractPath"]: n for n in result["nodes"]}
        self.assertEqual(nodes["/properties/x"]["status"], "type_rejected")
        self.assertEqual(nodes["/properties/x/items"]["reason"], "parent_type_rejected")
        self.assertEqual(result["errors"][0]["rule"], "type")

    def test_array_prefix_tail_and_repeated_paths(self):
        contract = {"type": "array", "prefixItems": [
            {"type": "integer"}, {"type": "boolean"}],
            "items": {"type": "string"}}
        short = audit.audit(contract, [2])
        nodes = {n["contractPath"]: n for n in short["nodes"]}
        self.assertEqual(nodes["/prefixItems/1"]["reason"], "array_too_short")
        self.assertEqual(nodes["/items"]["reason"], "no_tail_items")
        full = audit.audit(contract, [2, True, "a", "b"])
        tail = {n["contractPath"]: n for n in full["nodes"]}["/items"]
        self.assertEqual(tail["visits"], 2)
        self.assertEqual(tail["sampleDocumentPaths"], ["/2", "/3"])
        self.assertTrue(full["valid"])

    def test_exact_numbers_and_checker_errors(self):
        contract = b'{"type":"number","maximum":9007199254740992.0}'
        document = b'9007199254740993.0'
        result = audit.inspect(contract, document)
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["rule"], "maximum")
        self.assertEqual(result["counts"]["violations"], 1)
        self.assertEqual(result["nodes"][0]["status"], "exercised")

    def test_pins_checked_before_bad_json(self):
        with self.assertRaisesRegex(ValueError, "contract SHA-256 mismatch"):
            audit.inspect(b'not json', b'also not json', "0" * 64)

    def test_real_retained_zto_plan(self):
        contract = (ROOT / "line-2/tools/field-relations/window.contract.json").read_bytes()
        document = (ROOT / "line-2/tools/field-relations/window-plan.json").read_bytes()
        result = audit.inspect(contract, document)
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"]["dormant"], 0)
        self.assertEqual(result["counts"]["declaredNodes"], 17)

    def test_cli_reports_valid_and_invalid(self):
        contract = "line-2/tools/field-relations/window.contract.json"
        document = "line-2/tools/field-relations/window-plan.json"
        proc = subprocess.run([sys.executable, "-B", str(HERE / "audit.py"),
                               contract, document], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["complete"])


if __name__ == "__main__":
    unittest.main()
