import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL")
BASE_RPC_URL = os.getenv("BASE_RPC_URL")
OPTIMISM_RPC_URL = os.getenv("OPTIMISM_RPC_URL")
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")