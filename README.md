# Quest Agent — Airdrop Quests with Shared Memory (Meko)

**ContextCon: Remember Everything** · Theme: *Coding agents / Agentic support*

An airdrop-quest agent that **remembers** — across sessions and across agents.
It tracks quests, a burner wallet, and user progress in one shared context
layer: **[Meko](https://mekodata.ai)** by YugabyteDB. When you close the app
and come back tomorrow, it still knows which quests you finished, which
wallet you used, and what to do next — because that memory lives in Meko,
not in one chat window.

> ⚠️ Testnet / demo only. The agent tracks quest checklists; it never signs,
> broadcasts, or moves funds, and it never touches a real wallet.

## The problem

Airdrop farming is memory work: dozens of quests across chains, faucets,
social tasks, and check-ins, spread over weeks. A normal agent forgets
everything when the session ends. Users re-do quests, lose streaks, and
re-paste wallet addresses into random forms.

## The idea

One **Meko datapack** per project is the agent's shared memory:

| Meko capability | How this project uses it |
|---|---|
| **Memory** (`memory_add` / `memory_search`) | Durable facts: "user completed quest X with burner wallet 0x…", preferences, streaks |
| **Context search** (`context_search`) | Open-ended recall across memory + knowledge base + conversations |
| **Conversations** (`conversation_create` / `conversation_add_message`) | Full session history; Meko extracts durable facts from saved turns |
| **Knowledge base** (`knowledgebase_*`) | Quest guides / project docs, searchable later |
| **Decision traces** | Every suggestion and quest completion is logged with its reasoning and the memories it used — locally and as Meko conversations |
| **Datapack** | One isolated datapack (`contextcon-quest-agent`) shared by the CLI, the web dashboard, and any MCP client |

## Quick start (no Meko key needed for a local demo)

```bash
git clone <your-repo-url>
cd contextcon-quest-agent
python3 -m quest_agent init      # seeds 6 quests + creates a burner wallet
python3 -m quest_agent demo      # scripted end-to-end demo
python3 -m quest_agent status    # progress, wallet, recent memories
python3 -m quest_agent serve     # web dashboard at http://localhost:8000
python3 -m unittest discover -s tests   # 9 unit tests
```

Python 3.10+ only, **zero third-party dependencies** (stdlib only).

## Using it

```bash
python -m quest_agent quests                 # list quests + steps
python -m quest_agent start quest-daily-checkin
python -m quest_agent step quest-daily-checkin   # complete next step
python -m quest_agent chat "What should I do next?"
python -m quest_agent remember "I prefer Sepolia testnet quests"
python -m quest_agent recall "daily check-in quest"
python -m quest_agent meko-test              # check the Meko connection
```

The `chat` command shows the shared-memory loop in one turn: it recalls
relevant memories from Meko, suggests the next quest from your actual
progress, records a decision trace, and saves the turn as a Meko
conversation — so a *fresh* agent instance tomorrow recalls it.

## Connecting Meko Cloud (free)

The app runs without a key in **local-demo mode** (SQLite mirror in
`data/quest_agent.db`) and says so explicitly — it never pretends a Meko
write happened. To turn on real shared memory:

1. Create a free Meko account at https://cloud.mekodata.ai (Free plan:
   $0, 10 datapacks, 100 MB knowledge, no credit card).
2. Create a datapack named `contextcon-quest-agent` (one datapack per
   project — this is Meko's isolation unit).
3. **Settings → API Keys → Generate API key.** It starts with `mko_tkn_`
   and is shown once — copy it immediately.
4. `cp .env.example .env` and paste the key as `MEKO_API_KEY`. Optionally
   set `MEKO_DATAPACK_ID` to your datapack's id.
5. `python -m quest_agent meko-test` — it should list your datapacks and
   the 32 Meko MCP tools.

How it connects (official Meko docs — https://docs.mekodata.ai/use-meko/connect/):

* MCP endpoint: `https://mcp.mekodata.ai/mcp` (same for every account/datapack)
* Auth: `Authorization: Bearer <mko_tkn_…>` **plus** `User-Agent: meko-mcp-installer/1.0`
  — Meko rejects requests without either header.
* Tools used: `datapack_list`, `memory_add`, `memory_search`,
  `context_search`, `conversation_create`, `conversation_add_message`.
* Alternative official path: `npx @yugabytedb/meko-mcp@latest --client <client>
  --url "https://mcp.mekodata.ai/mcp"`, or the `.mcp.json` in this repo
  (paste your key there — never commit the filled-in file).

Free-tier limits (Meko docs): 1,000 conversation messages and 10,000
retrieval requests per month.

## Wallet safety

* A burner wallet is generated locally on first `init` with `secrets`
  (32 random bytes), its EVM address derived with pure-Python Keccak-256 +
  secp256k1 (`quest_agent/keccak.py`, verified against known test vectors).
* Stored in `data/burner_wallet.json` with mode `0600`. **The private key
  is never printed, logged, or returned by any user-facing function** —
  only the address and a masked preview (`ab12…9f34`) are shown.
* Testnet only. The agent performs no on-chain calls at all — quest steps
  are checklists the user does themselves. No mainnet, no real funds.
* `.env` and `data/` are gitignored. Rotate/revoke: delete
  `data/burner_wallet.json` and run `init` again for a fresh burner.

## Architecture

```
┌──────────────┐   MCP (JSON-RPC, Bearer + User-Agent)   ┌──────────────────┐
│  CLI / Web   │ ─────────────────────────────────────▶ │  Meko Cloud      │
│  quest_agent │   memory_add / memory_search /          │  datapack:       │
│  agent.py    │   context_search / conversation_*       │  contextcon-     │
│  memory.py   │                                         │  quest-agent     │
└──────┬───────┘                                         └──────────────────┘
       │  local mirror (always)
       ▼
┌──────────────┐
│  SQLite      │  memories · quests · progress · conversations · decision_traces
│  data/*.db   │  (works offline; Meko is the shared layer when configured)
└──────────────┘
```

| File | What it does |
|---|---|
| `quest_agent/meko_client.py` | Minimal MCP client (urllib, JSON-RPC over Streamable HTTP), official auth + tools |
| `quest_agent/memory.py` | Unified memory: Meko-first, local SQLite mirror always; honest mode reporting |
| `quest_agent/agent.py` | Orchestrator: recall → decide (decision trace) → act → persist |
| `quest_agent/quests.py` | Quest catalog (6 testnet/social/community quests) + progress logic |
| `quest_agent/store.py` | SQLite store: memories, quests, progress, conversations, traces |
| `quest_agent/wallet.py` | Burner wallet (testnet only), 0600 storage, never logs the key |
| `quest_agent/keccak.py` | Pure-Python Keccak-256 + secp256k1 (stdlib only) |
| `quest_agent/server.py` | Web dashboard + JSON API (stdlib `http.server`) |
| `quest_agent/__main__.py` | CLI: init / status / quests / start / step / remember / recall / chat / meko-test / demo / serve |
| `tests/` | `unittest` — Keccak + address vectors, wallet safety, quest flow, cross-session recall |

## How this meets the judging criteria

| Criterion (weight) | How it is met |
|---|---|
| **Use of Meko — 30%** | Meko is the context layer, not a bolt-on: every memory, conversation and decision trace goes through the official MCP tools into one datapack; the app degrades honestly to a local mirror without a key and reports its mode |
| **Impact & usefulness — 25%** | Solves a real, recurring pain for airdrop/quest farmers: lost progress, repeated quests, forgotten wallets — across sessions and agents |
| **Technical execution — 20%** | Runs end-to-end locally, stdlib-only, tested (Keccak/address vectors, wallet safety, quest flow, cross-session recall); real MCP client, not a mock |
| **Innovation — 15%** | Shared memory as the product: the same datapack serves the CLI, the web dashboard, and any MCP client (Claude/Cursor/Codex) |
| **Presentation — 10%** | Demo script in `docs/DEMO_SCRIPT.md`, web dashboard for the live demo, README + architecture above |

## Demo script

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — a <5 minute walkthrough:
setup → chat recalls memory → complete a quest → close the app → reopen
in a fresh session → it still remembers.

## ContextCon submission checklist

- [ ] Repo public on GitHub with setup instructions (this README)
- [ ] Recorded demo < 5 minutes (see `docs/DEMO_SCRIPT.md`)
- [ ] Project presentation + working demo link
- [ ] Theme: coding agents / agentic support
- [ ] Register on HackerEarth (needs the owner's real name, email, company,
      LinkedIn, GitHub — not included in this repo)

## Status / known limits

* Meko Cloud integration is implemented and the endpoint was verified
  live (unauthenticated probe → HTTP 401 `invalid_token`, as expected).
  A full end-to-end Meko write/read has **not** been run yet — it needs a
  real free API key (see "Connecting Meko Cloud" above).
* Quest steps are checklists, not automated on-chain execution — by design
  (safety rails: simulate + confirm before any real transaction).
* The MCP client speaks Streamable HTTP; if Meko ever requires SSE-only
  transport for a given client, `meko_client.py` is the one place to change.

## License

MIT — see [LICENSE](LICENSE).
