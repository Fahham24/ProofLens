import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    serpapi_key: str = os.getenv("SERPAPI_KEY", "").strip()
    polygon_rpc_url: str = os.getenv(
        "POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology/"
    ).strip()
    polygon_private_key: str = os.getenv("POLYGON_PRIVATE_KEY", "").strip()
    evidence_contract_address: str = os.getenv(
        "EVIDENCE_CONTRACT_ADDRESS", ""
    ).strip()

settings = Settings()
