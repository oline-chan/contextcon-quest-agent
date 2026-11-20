import tempfile
import unittest
from pathlib import Path

from quest_agent.keccak import keccak256, private_key_to_address
from quest_agent.wallet import ensure_burner_wallet, load_burner_wallet, public_info


class TestKeccak(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(
            keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_abc(self):
        self.assertEqual(
            keccak256(b"abc").hex(),
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
        )

    def test_privkey_1_address(self):
        # Known secp256k1 test vector: private key 1.
        self.assertEqual(
            private_key_to_address((1).to_bytes(32, "big")),
            "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf",
        )


class TestBurnerWallet(unittest.TestCase):
    def test_generate_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "burner_wallet.json"
            info, created = ensure_burner_wallet(path)
            self.assertTrue(created)
            self.assertTrue(info["address"].startswith("0x"))
            self.assertEqual(len(info["address"]), 42)
            # Private key is stored but never in the public info.
            self.assertNotIn("private_key_hex", info)
            self.assertIn("…", info["private_key_preview"])
            raw = load_burner_wallet(path)
            self.assertEqual(raw["address"], info["address"])
            self.assertEqual(len(raw["private_key_hex"]), 64)
            # Second ensure() must NOT overwrite the wallet.
            info2, created2 = ensure_burner_wallet(path)
            self.assertFalse(created2)
            self.assertEqual(info2["address"], info["address"])
            # File mode is 0600.
            self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")


if __name__ == "__main__":
    unittest.main()
