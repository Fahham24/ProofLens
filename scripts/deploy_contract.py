from __future__ import annotations

import json
import sys
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "EvidenceRegistry.sol"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))
from app.config import settings


def main():
    if not settings.polygon_private_key:
        raise SystemExit("Set POLYGON_PRIVATE_KEY in .env first.")

    source = CONTRACT_PATH.read_text(encoding="utf-8")

    print("Installing Solidity compiler 0.8.24 if needed...")
    install_solc("0.8.24")

    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "EvidenceRegistry.sol": {"content": source}
            },
            "settings": {
                "optimizer": {"enabled": True, "runs": 200},
                "outputSelection": {
                    "*": {
                        "*": ["abi", "evm.bytecode.object"]
                    }
                },
            },
        },
        solc_version="0.8.24",
    )

    contract_data = compiled["contracts"]["EvidenceRegistry.sol"]["EvidenceRegistry"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    (ARTIFACTS / "EvidenceRegistry.abi.json").write_text(
        json.dumps(abi, indent=2),
        encoding="utf-8",
    )

    w3 = Web3(Web3.HTTPProvider(settings.polygon_rpc_url))
    if not w3.is_connected():
        raise SystemExit("Could not connect to Polygon RPC.")

    account = w3.eth.account.from_key(settings.polygon_private_key)
    print("Deployer:", account.address)
    print("Chain ID:", w3.eth.chain_id)

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price

    tx = contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
            "gas": 1_000_000,
            "gasPrice": gas_price,
        }
    )

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("Deployment tx:", tx_hash.hex())

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    address = receipt.contractAddress

    print("\nDEPLOYED CONTRACT:")
    print(address)
    print("\nSave this in .env:")
    print(f"EVIDENCE_CONTRACT_ADDRESS={address}")
    print("\nExplorer:")
    print(f"https://amoy.polygonscan.com/address/{address}")


if __name__ == "__main__":
    main()
