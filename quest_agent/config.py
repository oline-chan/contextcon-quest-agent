"""Configuration for the Quest Agent.

All secrets come from the environment (or a local ``.env`` file that is
never committed). No default API key is shipped, and no key is ever logged.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "quest_agent.db"
BURNER_WALLET_PATH = DATA_DIR / "burner_wallet.json"

MEKO_MCP_URL = os.environ.get("MEKO_MCP_URL", "https://mcp.mekodata.ai/mcp")
MEKO_API_KEY = os.environ.get("MEKO_API_KEY", "").strip()
# One datapack per project (Meko isolation unit). Empty = use the account's
# default datapack; set MEKO_DATAPACK_ID after creating the datapack
# "contextcon-quest-agent" in the Meko portal.
MEKO_DATAPACK_ID = os.environ.get("MEKO_DATAPACK_ID", "").strip() or None
MEKO_AGENT_ID = os.environ.get("MEKO_AGENT_ID", "quest-agent")
MEKO_TIMEOUT_S = float(os.environ.get("MEKO_TIMEOUT_S", "30"))

USER_ID = os.environ.get("QUEST_AGENT_USER", "local-user")


def load_dotenv() -> None:
    """Load ``.env`` in the project root if present (values never logged)."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def meko_configured() -> bool:
    return bool(MEKO_API_KEY)
