# Demo narration — Quest Agent (ContextCon) — ENGLISH, ready to record

> **Status: DRAFT narration for the demo video draft.** Target length: **under 5 minutes**
> (spoken time below ≈ 3 min 30 s at a natural pace; the video draft is a 2:30 silent
> slideshow cut to the same structure — record the voiceover over it for the final cut).
> Submission deadline: **17 January 2027, 23:59 PT**. Theme: coding agents / agentic support.
>
> How to record: read each block in one take, pausing at the `[...]` beats. Keep the
> terminal / dashboard on screen for the matching section. Do not read the bracketed
> stage directions aloud.

---

## 0:00–0:25 — The problem

> "Quest farming is memory work. Dozens of quests, spread across chains, faucets,
> social tasks and check-ins — stretched over weeks. A normal agent forgets
> everything the moment the session ends. So users redo quests, lose streaks,
> and paste their wallet address into random forms, again and again.
>
> This agent remembers — because its memory doesn't live in one chat window.
> It lives in Meko."
>
> *[On screen: title slide — "Quest Agent — Airdrop quests with shared memory (Meko)",
> ContextCon: Remember Everything.]*

## 0:25–0:55 — Setup (30 s)

> "Setup takes thirty seconds, and it needs no API key to try. One command seeds
> six quests and creates a burner wallet, just for testnets. The address is shown;
> the private key is never shown, never logged — it lives in a file only this
> machine can read. And the agent tells you honestly which memory mode it is in:
> local mirror now, Meko Cloud once you add a free key."
>
> *[On screen: terminal — `python -m quest_agent init`, then `status`.
> Point at: "6 quests seeded", the burner wallet address, "Memory mode: local".]*

```bash
python -m quest_agent init
python -m quest_agent status
```

## 0:55–1:55 — The shared-memory loop (60 s)

> "Here is the loop that makes it an agent, not a checklist. I ask it what to do
> next. It recalls my memories, looks at my real progress, and suggests the next
> quest — the daily check-in streak. I start it, and I complete a step.
> Every step writes a decision trace: what it decided, why, and which memories
> it used. And when the quest is done, that fact is saved as a durable memory:
> 'User completed the daily check-in quest with burner wallet 0x635c…B7D36.
> Earned 15 points.'"
>
> *[On screen: terminal — `chat "What should I do next?"`, `start`, `step`.
> Point at the decision trace and the saved memory line.]*

```bash
python -m quest_agent chat "What should I do next?"
python -m quest_agent start quest-daily-checkin
python -m quest_agent step quest-daily-checkin
```

## 1:55–2:40 — It remembers across sessions (45 s)

> "Now the part that matters. I close the terminal. I open a brand-new session —
> a fresh agent that has never met me. I ask it to recall the daily check-in quest.
> And there it is: the completed quest, the wallet, the fifteen points. One out of
> six quests done. Nothing was re-pasted, nothing was re-done. That is the Meko
> datapack working: one shared memory, across sessions — and across agents,
> because any agent on the same datapack sees the same facts."
>
> *[On screen: fresh terminal — `recall "daily check-in quest"`, then `status`
> showing 1/6 done, 15 of 65 points.]*

```bash
python -m quest_agent recall "daily check-in quest"
python -m quest_agent status
```

## 2:40–3:25 — Web dashboard (45 s)

> "The same memory is also a web dashboard. Same quests, same progress, same
> wallet, same memories and decision traces — plus a chat box. The CLI, the
> dashboard, and any MCP client all read and write the same datapack, so there
> is no 'which copy is true?' — there is one memory."
>
> *[On screen: `python -m quest_agent serve`, browser at http://localhost:8000,
> then the JSON endpoints `/api/status`, `/api/quests`, `/api/traces`.]*

```bash
python -m quest_agent serve   # http://localhost:8000
```

## 3:25–3:50 — Meko, honestly (25 s)

> "And a word on honesty, because it is part of the design. With a free Meko API
> key, `meko-test` lists your datapacks and the thirty-two MCP tools, and every
> memory goes to Meko Cloud over the official MCP endpoint. Without a key, the app
> says so — out loud — and runs on a local SQLite mirror. It never pretends a
> Meko write happened. One datapack per project, shared memory for every agent.
> That is Quest Agent. Thank you."
>
> *[On screen: `python -m quest_agent meko-test` + architecture diagram slide:
> CLI / Web → MCP (Bearer + User-Agent) → Meko datapack `contextcon-quest-agent`,
> with the local SQLite mirror underneath.]*

```bash
python -m quest_agent meko-test
```

---

## Who this is for

- **Airdrop / quest farmers** who juggle dozens of quests across chains and weeks and
  keep losing track of what is done, which wallet they used, and what is next.
- **Agent builders** who need their coding agents and support agents to share context
  instead of each starting from zero every session.
- **Hackathon judges and the Meko / YugabyteDB team**: a small, stdlib-only, fully
  testable example of Meko as the context layer — memory, context search,
  conversations, knowledge base, and decision traces in one datapack.

## How Meko is used (one-paragraph version for the video description)

Quest Agent stores every durable fact in one Meko datapack,
`contextcon-quest-agent`, through the official MCP endpoint
(`https://mcp.mekodata.ai/mcp`, `Authorization: Bearer mko_tkn_…` plus
`User-Agent: meko-mcp-installer/1.0`): `memory_add` / `memory_search` for durable
facts such as completed quests and wallet use, `context_search` for open-ended
recall across memory, knowledge base and conversations, and
`conversation_create` / `conversation_add_message` for full session history from
which Meko extracts durable facts. Decision traces are logged with their
reasoning and the memories they used. Without a key the app runs on a local
SQLite mirror and says so — it never fakes a Meko write.

## Recording checklist (final cut)

- [ ] Re-run `python -m quest_agent demo` from a clean state so the recording shows 0/6 → 1/6 live
- [ ] Record voiceover from this script (English, ~3:30) over the screen capture
- [ ] Capture the real dashboard at http://localhost:8000 (replace draft slide 5)
- [ ] With a real free Meko key in `.env`, re-record the `meko-test` + `chat` segment in Meko mode
- [ ] Export final < 5 minutes, 1280×720 or 1920×1080, check audio levels, add captions
- [ ] Keep the final video file out of the repo if it is large (link it in the README instead)
