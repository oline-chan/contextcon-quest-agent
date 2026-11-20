"""CLI for the ContextCon Quest Agent.

Usage (from the project root):
    python -m quest_agent init        # seed quests + create burner wallet
    python -m quest_agent status      # progress, wallet, recent memories
    python -m quest_agent quests      # list all quests
    python -m quest_agent start <id>  # start a quest
    python -m quest_agent step <id>   # complete the next step of a quest
    python -m quest_agent remember "fact to remember"
    python -m quest_agent recall "query"
    python -m quest_agent chat "message"
    python -m quest_agent meko-test   # check the Meko MCP connection
    python -m quest_agent serve       # local web dashboard on :8000
    python -m quest_agent demo        # scripted end-to-end demo (no key needed)

No command ever prints a private key. Wallet output shows the address
and a masked key preview only.
"""
import argparse
import json
import sys

from . import agent as agent_mod
from . import config, meko_client, quests, store, wallet


def _print(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _agent():
    config.load_dotenv()
    # Re-read env after .env load (config values are read at import time,
    # so re-apply here for the CLI path).
    import importlib
    importlib.reload(config)
    return agent_mod.QuestAgent()


def cmd_init(args):
    ag = _agent()
    out = ag.setup()
    print(f"Seeded {out['seeded_quests']} quests.")
    print(f"Burner wallet: {out['wallet']['address']} "
          f"({'created' if out['wallet_created'] else 'already existed'})")
    print(f"Memory mode: {ag.memory.mode} "
          f"({'Meko Cloud' if ag.memory.mode == 'meko' else 'local mirror — set MEKO_API_KEY to use Meko Cloud'})")
    print("Never share the burner private key. It lives in data/burner_wallet.json (0600).")


def cmd_status(args):
    _print(_agent().status())


def cmd_quests(args):
    ag = _agent()
    for q in ag.list_quests():
        mark = {"todo": "[ ]", "in_progress": "[~]", "done": "[x]"}[q["status"]]
        print(f"{mark} {q['id']} — {q['title']} ({q['chain']}, {q['reward_points']} pts)")
        print(f"    {q['description']}")
        for i, step in enumerate(q["steps"]):
            done = "x" if i < q["steps_done"] else " "
            print(f"      [{done}] {step}")
        print(f"    Risk: {q['risk_note']}")


def cmd_start(args):
    _print(_agent().start_quest(args.quest_id))


def cmd_step(args):
    _print(_agent().complete_step(args.quest_id))


def cmd_remember(args):
    ag = _agent()
    saved = ag.memory.remember(args.text)
    print(f"Remembered ({'Meko + local' if saved['meko'] else 'local mirror only'}): {args.text}")


def cmd_recall(args):
    ag = _agent()
    results = ag.memory.recall(args.query)
    if not results:
        print("No memories found.")
        return
    for r in results:
        print(f"[{r['source']}] {r['text']}")


def cmd_chat(args):
    ag = _agent()
    print(ag.chat(args.message)["answer"])


def cmd_meko_test(args):
    config.load_dotenv()
    import importlib
    importlib.reload(config)
    if not config.meko_configured():
        print("Meko is NOT configured (no MEKO_API_KEY).")
        print("App runs in local-demo mode. To connect Meko Cloud:")
        print("  1. Create a free account at https://cloud.mekodata.ai")
        print("  2. Create a datapack named 'contextcon-quest-agent'")
        print("  3. Settings > API Keys > Generate API key (starts with mko_tkn_)")
        print("  4. Copy .env.example to .env and paste the key as MEKO_API_KEY")
        return
    client = meko_client.MekoClient()
    try:
        info = client.initialize()
        print(f"Meko MCP connected. Server: {info.get('serverInfo', {}).get('name', '?')}")
        tools = client.list_tools()
        print(f"Tools available ({len(tools)}): {', '.join(tools[:12])}...")
        packs = client.datapack_list()
        print(f"Datapacks: {packs}")
    except meko_client.MekoAuthError as exc:
        print(f"AUTH FAILED: {exc}")
        sys.exit(1)
    except meko_client.MekoError as exc:
        print(f"Meko error: {exc}")
        sys.exit(1)


def cmd_demo(args):
    """Scripted demo: setup -> chat -> start quest -> complete it -> recall."""
    ag = _agent()
    print("== 1. Setup ==")
    cmd_init(args)
    print("\n== 2. Chat (agent recalls memory, suggests next quest) ==")
    print(ag.chat("What should I do next?")["answer"])
    print("\n== 3. Start + complete the daily check-in quest ==")
    _print(ag.start_quest("quest-daily-checkin"))
    for _ in range(7):
        out = ag.complete_step("quest-daily-checkin")
    _print({k: out[k] for k in ("ok", "completed", "memory_saved_to_meko")})
    print("\n== 4. Recall in a fresh agent instance (memory survives sessions) ==")
    fresh = agent_mod.QuestAgent()
    for r in fresh.memory.recall("daily check-in quest"):
        print(f"[{r['source']}] {r['text']}")
    print("\n== 5. Status ==")
    _print(fresh.status()["progress"])


def cmd_serve(args):
    from .server import serve
    serve(port=args.port)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="quest-agent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("quests")
    p = sub.add_parser("start"); p.add_argument("quest_id")
    p = sub.add_parser("step"); p.add_argument("quest_id")
    p = sub.add_parser("remember"); p.add_argument("text")
    p = sub.add_parser("recall"); p.add_argument("query")
    p = sub.add_parser("chat"); p.add_argument("message")
    sub.add_parser("meko-test")
    sub.add_parser("demo")
    p = sub.add_parser("serve"); p.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    {
        "init": cmd_init, "status": cmd_status, "quests": cmd_quests,
        "start": cmd_start, "step": cmd_step, "remember": cmd_remember,
        "recall": cmd_recall, "chat": cmd_chat, "meko-test": cmd_meko_test,
        "demo": cmd_demo, "serve": cmd_serve,
    }[args.command](args)


if __name__ == "__main__":
    main()
