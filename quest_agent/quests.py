"""Quest catalog: airdrop / testnet quests the agent tracks.

These are generic, public, testnet-only quest templates (no real funds,
no mainnet, no chain calls). Each quest is a checklist; the agent tracks
progress and remembers it across sessions via Meko + the local mirror.
Real quest URLs / contract addresses are intentionally NOT hardcoded —
the user adds them per quest when they are verified.
"""
from . import store

SEED_QUESTS = [
    {
        "id": "testnet-faucet-sepolia",
        "title": "Claim Sepolia testnet faucet",
        "category": "testnet",
        "chain": "Ethereum Sepolia (testnet)",
        "description": "Get testnet ETH from a public faucet into the burner wallet so later testnet quests can pay gas (testnet only, worthless).",
        "steps": ["Open a public Sepolia faucet", "Paste burner wallet address", "Confirm testnet ETH received"],
        "reward_points": 10,
        "risk_note": "Testnet only. Never paste a real wallet's private key into any faucet.",
    },
    {
        "id": "testnet-faucet-bsc",
        "title": "Claim BSC testnet faucet",
        "category": "testnet",
        "chain": "BNB Smart Chain testnet",
        "description": "Get tBNB from the BSC testnet faucet into the burner wallet.",
        "steps": ["Open the BSC testnet faucet", "Paste burner wallet address", "Confirm tBNB received"],
        "reward_points": 10,
        "risk_note": "Testnet only. tBNB has no real value.",
    },
    {
        "id": "quest-social-follow",
        "title": "Follow the project + repost the quest announcement",
        "category": "social",
        "chain": "off-chain",
        "description": "Standard social quest: follow the project's official account and repost its quest post from the account linked to the burner profile.",
        "steps": ["Follow the official account", "Repost the quest announcement", "Save the post link as proof"],
        "reward_points": 5,
        "risk_note": "Only interact with verified official accounts. Never click links from DMs.",
    },
    {
        "id": "quest-testnet-swap",
        "title": "Do a testnet swap on a testnet DEX",
        "category": "on-chain",
        "chain": "Ethereum Sepolia (testnet)",
        "description": "Swap a small amount of testnet ETH for a testnet token on a testnet DEX, using the burner wallet only.",
        "steps": ["Connect burner wallet to the testnet DEX", "Swap a small testnet amount", "Save the testnet tx hash as proof"],
        "reward_points": 20,
        "risk_note": "Testnet only. Simulate / check the contract first; never approve unlimited spending.",
    },
    {
        "id": "quest-join-community",
        "title": "Join the community (Discord / Telegram)",
        "category": "community",
        "chain": "off-chain",
        "description": "Join the project's official Discord or Telegram and verify the burner profile in the quest channel.",
        "steps": ["Join via the official invite link", "Verify in the quest channel", "Note your username in the agent"],
        "reward_points": 5,
        "risk_note": "Never share a seed phrase or private key with any 'support' account.",
    },
    {
        "id": "quest-daily-checkin",
        "title": "Daily check-in streak (7 days)",
        "category": "habit",
        "chain": "off-chain",
        "description": "Check in once a day for 7 days. The agent remembers the streak across sessions — that is the shared-memory demo.",
        "steps": ["Check in day 1", "Check in day 2", "Check in day 3", "Check in day 4", "Check in day 5", "Check in day 6", "Check in day 7"],
        "reward_points": 15,
        "risk_note": "No funds involved.",
    },
]


def seed_quests(conn):
    for quest in SEED_QUESTS:
        store.upsert_quest(conn, quest)
    return len(SEED_QUESTS)


def progress_summary(conn):
    quests = store.list_quests(conn)
    total = len(quests)
    done = sum(1 for q in quests if q["status"] == "done")
    points = sum(q["reward_points"] for q in quests if q["status"] == "done")
    total_points = sum(q["reward_points"] for q in quests)
    return {
        "total": total,
        "done": done,
        "in_progress": sum(1 for q in quests if q["status"] == "in_progress"),
        "todo": sum(1 for q in quests if q["status"] == "todo"),
        "points": points,
        "total_points": total_points,
    }


def next_quest(conn):
    """Suggest the next quest: in-progress first, then the first todo."""
    quests = store.list_quests(conn)
    for q in quests:
        if q["status"] == "in_progress":
            return q
    for q in quests:
        if q["status"] == "todo":
            return q
    return None
