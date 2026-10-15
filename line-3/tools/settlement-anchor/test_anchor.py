import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("anchor", HERE / "anchor.py")
anchor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anchor)


def demo():
    return json.loads((HERE / "demo-anchor.json").read_text())


class AnchorTests(unittest.TestCase):
    def test_demo_anchors(self):
        result = anchor.anchor(demo())
        self.assertTrue(result["anchored"])
        self.assertEqual(result["transactionIndex"], 181)

    def test_block_mismatch_is_not_anchored(self):
        bundle = demo()
        bundle["position"]["block"]["hash"] = "0x" + "ab" * 32
        result = anchor.anchor(bundle)
        self.assertEqual(result["state"], "block_anchor_mismatch")

    def test_wrong_transaction_refuses(self):
        bundle = demo()
        bundle["position"]["transactionHash"] = "0x" + "ab" * 32
        with self.assertRaises(anchor.AnchorError):
            anchor.anchor(bundle)

    def test_finality_is_required(self):
        bundle = demo()
        bundle["settlement"]["finalized"] = False
        self.assertEqual(anchor.anchor(bundle)["state"], "finality_policy_failed")

    def test_confirmation_math_is_bound(self):
        bundle = demo()
        bundle["settlement"]["confirmations"] = 12
        self.assertEqual(anchor.anchor(bundle)["state"], "confirmation_policy_failed")

    def test_reverted_verdict_does_not_pass(self):
        bundle = demo()
        bundle["settlement"]["settled"] = False
        self.assertEqual(anchor.anchor(bundle)["state"], "settlement_not_accepted")

    def test_duplicate_keys_refused(self):
        with self.assertRaises(anchor.AnchorError):
            anchor.strict_json(b'{"policy":{},"policy":{},"settlement":{},"position":{}}')

    def test_loader_reads_at_most_limit_plus_one(self):
        scratch = Path("test/scratch")
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            item = Path(directory) / "bundle.json"
            relative = item.relative_to(Path.cwd()).as_posix()
            item.write_bytes(b"x" * anchor.MAX_BYTES)
            self.assertEqual(len(anchor.load(relative)), anchor.MAX_BYTES)
            item.write_bytes(b"x" * (anchor.MAX_BYTES + 1))
            with self.assertRaisesRegex(anchor.AnchorError, "exceeds 100 KB"):
                anchor.load(relative)

    def test_loader_refuses_symlink_and_special_file(self):
        scratch = Path("test/scratch")
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            folder = Path(directory)
            target = folder / "bundle.json"
            target.write_bytes(b"{}")
            link = folder / "link.json"
            link.symlink_to(target.name)
            with self.assertRaises(anchor.AnchorError):
                anchor.load(link.relative_to(Path.cwd()).as_posix())
            fifo = folder / "pipe.json"
            os.mkfifo(fifo)
            with self.assertRaises(anchor.AnchorError):
                anchor.load(fifo.relative_to(Path.cwd()).as_posix())

    def test_loader_refuses_traversal_and_hidden_paths(self):
        for name in ("../bundle.json", "/tmp/bundle.json", "test//bundle.json",
                     "test/./bundle.json", "test/.hidden/bundle.json"):
            with self.subTest(name=name), self.assertRaises(anchor.AnchorError):
                anchor.load(name)


if __name__ == "__main__":
    unittest.main()
