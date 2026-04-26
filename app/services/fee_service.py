import json
import time
from pathlib import Path

import requests
from web3 import Web3
from app.core.config import (
    ETHEREUM_RPC_URL,
    ARBITRUM_RPC_URL,
    BASE_RPC_URL,
    OPTIMISM_RPC_URL,
    POLYGON_RPC_URL,
)

TRANSFER_GAS_UNITS = 65000
CACHE_TTL_SECONDS = 15
PRICE_CACHE_TTL_SECONDS = 60
HISTORY_FILE = Path("data/fee_history.json")

_fee_cache = {
    "timestamp": 0,
    "data": None
}

_price_cache = {
    "timestamp": 0,
    "eth_usd": None,
    "matic_usd": None
}

CHAINS = {
    "ethereum": {
        "rpc_url": ETHEREUM_RPC_URL,
        "native_token_symbol": "ETH"
    },
    "arbitrum": {
        "rpc_url": ARBITRUM_RPC_URL,
        "native_token_symbol": "ETH"
    },
    "base": {
        "rpc_url": BASE_RPC_URL,
        "native_token_symbol": "ETH"
    },
    "optimism": {
        "rpc_url": OPTIMISM_RPC_URL,
        "native_token_symbol": "ETH"
    },
    "polygon": {
        "rpc_url": POLYGON_RPC_URL,
        "native_token_symbol": "MATIC"
    }
}


def _get_native_prices_usd():
    now = time.time()

    if (
        _price_cache["eth_usd"] is not None and
        _price_cache["matic_usd"] is not None and
        now - _price_cache["timestamp"] < PRICE_CACHE_TTL_SECONDS
    ):
        return {
            "ETH": _price_cache["eth_usd"],
            "MATIC": _price_cache["matic_usd"]
        }

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,polygon-ecosystem-token&vs_currencies=usd",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        eth_usd = float(data["ethereum"]["usd"])
        matic_usd = float(data["polygon-ecosystem-token"]["usd"])

        _price_cache["timestamp"] = now
        _price_cache["eth_usd"] = eth_usd
        _price_cache["matic_usd"] = matic_usd

        return {
            "ETH": eth_usd,
            "MATIC": matic_usd
        }

    except Exception:
        eth_fallback = _price_cache["eth_usd"] if _price_cache["eth_usd"] is not None else 2200.0
        matic_fallback = _price_cache["matic_usd"] if _price_cache["matic_usd"] is not None else 1.0

        return {
            "ETH": eth_fallback,
            "MATIC": matic_fallback
        }


def _get_chain_fee(chain_name: str, rpc_url: str, native_token_symbol: str, native_token_price_usd: float):
    if not rpc_url:
        return {
            "chain": chain_name,
            "status": "error",
            "error": "Missing RPC URL"
        }

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))

        if not w3.is_connected():
            return {
                "chain": chain_name,
                "status": "error",
                "error": "RPC connection failed"
            }

        gas_price_wei = w3.eth.gas_price
        latest_block = w3.eth.block_number

        gas_gwei = w3.from_wei(gas_price_wei, "gwei")
        estimated_native_cost = (gas_price_wei * TRANSFER_GAS_UNITS) / 10**18
        estimated_usd = float(estimated_native_cost) * native_token_price_usd

        return {
            "chain": chain_name,
            "status": "ok",
            "rpc_used": rpc_url,
            "latest_block": latest_block,
            "gas_gwei": round(float(gas_gwei), 6),
            "native_token_symbol": native_token_symbol,
            "native_token_price_usd": round(native_token_price_usd, 6),
            "estimated_usd": round(estimated_usd, 6)
        }

    except Exception as e:
        return {
            "chain": chain_name,
            "status": "error",
            "error": str(e)
        }


def _append_history(snapshot: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []

    history.append(snapshot)
    history = history[-500:]

    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_fee_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _fetch_all_fees():
    results = {}
    prices = _get_native_prices_usd()

    for chain_name, cfg in CHAINS.items():
        symbol = cfg["native_token_symbol"]
        native_price = prices.get(symbol, 0)

        results[chain_name] = _get_chain_fee(
            chain_name=chain_name,
            rpc_url=cfg["rpc_url"],
            native_token_symbol=symbol,
            native_token_price_usd=native_price
        )

    snapshot = {
        "timestamp": int(time.time()),
        "fees": results
    }
    _append_history(snapshot)

    return results


def get_current_fees():
    now = time.time()

    if (
        _fee_cache["data"] is not None and
        now - _fee_cache["timestamp"] < CACHE_TTL_SECONDS
    ):
        return _fee_cache["data"]

    fresh_data = _fetch_all_fees()
    _fee_cache["timestamp"] = now
    _fee_cache["data"] = fresh_data

    return fresh_data