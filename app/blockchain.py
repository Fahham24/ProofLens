from __future__ import annotations

import json
from pathlib import Path

from web3 import Web3


ABI_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "EvidenceRegistry.abi.json"


def load_abi():
    with open(ABI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def connect(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        raise RuntimeError("Could not connect to Polygon RPC.")
    return w3


def get_contract(w3: Web3, address: str):
    if not address:
        raise ValueError("EVIDENCE_CONTRACT_ADDRESS is missing.")
    return w3.eth.contract(
        address=Web3.to_checksum_address(address),
        abi=load_abi(),
    )


def anchor_evidence(
    *,
    rpc_url: str,
    private_key: str,
    contract_address: str,
    evidence_hash_hex: str,
) -> dict:
    if not private_key:
        raise ValueError("POLYGON_PRIVATE_KEY is missing.")
    if not evidence_hash_hex or len(evidence_hash_hex) != 64:
        raise ValueError("Evidence hash must be a 64-character SHA-256 hex string.")

    w3 = connect(rpc_url)
    account = w3.eth.account.from_key(private_key)
    contract = get_contract(w3, contract_address)

    nonce = w3.eth.get_transaction_count(account.address)
    chain_id = w3.eth.chain_id

    hash_bytes = bytes.fromhex(evidence_hash_hex)

    tx = contract.functions.registerEvidence(hash_bytes).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 150_000,
            "maxFeePerGas": w3.to_wei("50", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        }
    )

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    return {
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "status": int(receipt.status),
        "submitter": account.address,
        "chain_id": chain_id,
    }


def verify_on_chain(
    *,
    rpc_url: str,
    contract_address: str,
    record_id: int,
    expected_hash_hex: str,
) -> dict:
    w3 = connect(rpc_url)
    contract = get_contract(w3, contract_address)

    record = contract.functions.getEvidence(record_id).call()
    # Solidity returns: evidenceHash, timestamp, submitter
    stored_hash = "0x" + bytes(record[0]).hex()

    expected = "0x" + expected_hash_hex.lower().removeprefix("0x")
    return {
        "record_id": record_id,
        "stored_hash": stored_hash,
        "expected_hash": expected,
        "valid": stored_hash.lower() == expected.lower(),
        "timestamp": int(record[1]),
        "submitter": record[2],
        "chain_id": w3.eth.chain_id,
    }
