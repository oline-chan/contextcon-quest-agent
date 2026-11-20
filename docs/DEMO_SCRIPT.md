# Demo script — ContextCon Quest Agent (< 5 minutes)

Target: a recorded walkthrough for the ContextCon submission (video < 5 min),
plus the same flow for a live finalist demo.

## 0:00–0:30 — The problem (30s)
"Quest farming is memory work. Dozens of quests, weeks apart, across chains.
Normal agents forget everything when the session ends — so users redo quests
and lose streaks. This agent remembers, because its memory lives in Meko."

Show the HackerEarth theme: coding agents / agentic support.

## 0:30–1:30 — Setup (60s)
```bash
python -m quest_agent init
python -m quest_agent status
```
Point out: 6 quests seeded, burner wallet created (address shown, private key
never shown), memory mode reported honestly — "local" without a key,
"Meko" with one.

## 1:30–2:30 — The shared-memory loop (60s)
```bash
python -m quest_agent chat "What should I do next?"
python -m quest_agent start quest-daily-checkin
python -m quest_agent step quest-daily-checkin   # repeat to finish it
```
Narrate: chat recalls memories, suggests the next quest from real progress,
each step writes a decision trace, completing the quest saves a durable
memory ("User completed quest …") to Meko.

## 2:30–3:30 — It remembers across sessions (60s)
Close the terminal. Open a **fresh** one and run:
```bash
python -m quest_agent recall "daily check-in quest"
python -m quest_agent status
```
The fresh instance recalls the completed quest and the streak — that is the
Meko datapack working: memory shared across sessions (and across agents on
the same datapack).

## 3:30–4:30 — Web dashboard (60s)
```bash
python -m quest_agent serve
```
Open http://localhost:8000: quests, progress, wallet address, recent
memories, decision traces, chat box — same memory as the CLI.

## 4:30–5:00 — Meko, honestly (30s)
```bash
python -m quest_agent meko-test
```
With a free Meko API key: lists datapacks + tools. Without one, the app says
so and runs on the local mirror. End on the architecture: one datapack,
`memory_*` / `context_search` / `conversation_*` over the official MCP
endpoint `https://mcp.mekodata.ai/mcp`.
