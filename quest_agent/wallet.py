"""Burner wallet for testnet quests ONLY.

Safety rules (On-Chain Safety Rails):
* This wallet is generated locally, for testnet / demo quests only.
* It is NEVER the user's real wallet. No real funds, no mainnet.
* The private key is stored in ``data/burner_wallet.json`` with mode 0600
  and is NEVER printed, logged, or returned by any function in this module.
  Only the address (and a masked key preview) ever leaves this module.
* The agent never signs or broadcasts a transaction. Quest steps are
  tracked (checklist), not executed on-chain by this code.

If you need real on-chain execution later, do it through a proper signer
with simulation + explicit user confirmation — not through this module.
"""
import json
import os
import secrets

from . import config
from .keccak import private_key_to_address


class WalletError(Exception):
    pass


def generate_burner_wallet(path=None):
    """Create a fresh burner wallet and store it (mode 0600)."""
    path = path or config.BURNER_WALLET_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise WalletError(f"Burner wallet already exists at {path} — refusing to overwrite it.")
    private_key = secrets.token_bytes(32)
    address = private_key_to_address(private_key)
    payload = {
        "network": "testnet-only",
        "address": address,
        # Private key is stored, never printed. Keep this file 0600.
        "private_key_hex": private_key.hex(),
        "warning": "BURNER wallet for testnet/demo only. Never send real funds here.",
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    os.chmod(path, 0o600)
    return address


def load_burner_wallet(path=None):
    """Return {'address': ..., 'private_key_hex': ...} or None if absent.

    Callers must never print or log the private key. Use ``public_info()``
    for anything user-facing.
    """
    path = path or config.BURNER_WALLET_PATH
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "private_key_hex" not in data or "address" not in data:
        raise WalletError(f"Burner wallet file {path} is malformed.")
    return data


def public_info(path=None):
    """User-facing wallet info: address + masked key preview only."""
    wallet = load_burner_wallet(path)
    if wallet is None:
        return None
    key = wallet["private_key_hex"]
    return {
        "address": wallet["address"],
        "network": wallet.get("network", "testnet-only"),
        "private_key_preview": f"{key[:4]}…{key[-4:]} (stored locally, mode 0600, never shown in full)",
    }


def ensure_burner_wallet(path=None):
    """Return public info, generating a fresh burner wallet if none exists."""
    info = public_info(path)
    if info is not None:
        return info, False
    address = generate_burner_wallet(path)
    return public_info(path), True
