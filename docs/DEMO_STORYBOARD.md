# Demo storyboard — Quest Agent (ContextCon) — frame by frame

> **Status: DRAFT.** Frames are rendered slides (`docs/demo-frames/frame-N.png`),
> assembled into the silent video draft `docs/demo-draft.mp4` (1280×720, 3:50).
> A real browser screenshot of the dashboard was **not** possible from this VM:
> subagents have no live browser, and Playwright/Chromium is blocked by the VM
> egress proxy (known limitation). For the final cut, replace frame 5 with a real
> screen capture of http://localhost:8000 and record the voiceover from
> `docs/DEMO_NARRATION.md`. Total storyboard time 3:50 — under the 5-minute limit.
>
> Voiceover: `docs/DEMO_NARRATION.md` (English, ≈3:30 spoken). Terminal evidence:
> `docs/demo-run-2026-11-20.log`.

## Frame list

| # | Time | Visual (file) | On-screen text | Voiceover (narration §) | Action on screen (final cut) |
|---|------|---------------|----------------|--------------------------|------------------------------|
| 1 | 0:00–0:25 (25 s) | `demo-frames/frame-1.png` — title slide | "Quest Agent — Airdrop quests with shared memory (Meko)" / "ContextCon: Remember Everything" | §0:00 — The problem: quest farming is memory work; normal agents forget; this one remembers because its memory lives in Meko. | Title card over terminal. No typing. |
| 2 | 0:25–0:55 (30 s) | `demo-frames/frame-2.png` — setup | `$ python -m quest_agent init` / `$ python -m quest_agent status` / "6 quests seeded · burner wallet created · private key NEVER shown" | §0:25 — Setup in 30 s, no key needed; burner wallet testnet-only; mode reported honestly (local / Meko). | Type `init`, then `status`. Point at "6 quests seeded", wallet address, "Memory mode: local". |
| 3 | 0:55–1:55 (60 s) | `demo-frames/frame-3.png` — shared-memory loop | `chat "What should I do next?"` → "Next quest: Daily check-in streak (7 days)" / `step quest-daily-checkin` | §0:55 — The loop: recall → suggest from real progress → step → decision trace → durable memory ("…Earned 15 points."). | Run `chat`, `start`, `step` live. Highlight the decision trace + saved-memory line. |
| 4 | 1:55–2:40 (45 s) | `demo-frames/frame-4.png` — cross-session recall | `recall "daily check-in quest"` → "[local] User completed quest 'Daily check-in streak (7 days)' … Earned 15 points." / "1/6 done, 15/65 pts" | §1:55 — Close the terminal, open a fresh session; it still knows — quest, wallet, points. One datapack, shared across sessions and agents. | **Close the terminal window on camera**, open a new one, run `recall` + `status`. This is the money shot — do not fake it with the same window. |
| 5 | 2:40–3:25 (45 s) | `demo-frames/frame-5.png` — dashboard (DRAFT slide; replace with real capture) | `python -m quest_agent serve → http://localhost:8000` / `GET /api/status · /api/quests · /api/traces · POST /api/chat` | §2:40 — Same memory in the browser: quests, progress, wallet, memories, traces, chat. CLI, dashboard, any MCP client — one datapack. | Open http://localhost:8000 live; click "Complete next step" once; show `/api/status` JSON in a second tab. |
| 6 | 3:25–3:50 (25 s) | `demo-frames/frame-6.png` — Meko, honestly | `memory_add · memory_search · context_search · conversation_*` / `MCP: https://mcp.mekodata.ai/mcp` | §3:25 — With a free key: real Meko Cloud. Without one: the app says so and runs on a local mirror — never pretends. "Thank you." | Run `meko-test` (in Meko mode if the key is ready, otherwise show the honest local-mode message). End card: repo URL + "Quest Agent · ContextCon". |

## Timing check

| Segment | Duration | Running total |
|---|---|---|
| 1 Problem | 0:25 | 0:25 |
| 2 Setup | 0:30 | 0:55 |
| 3 Shared-memory loop | 1:00 | 1:55 |
| 4 Cross-session recall | 0:45 | 2:40 |
| 5 Dashboard | 0:45 | 3:25 |
| 6 Meko, honestly | 0:25 | **3:50** |

Limit: < 5:00. Margin: 1:10 spare for pauses / retakes.

## Video draft spec

- File: `docs/demo-draft.mp4` — 1280×720, 30 fps, H.264 + silent AAC audio track,
  3:50 (230 s). Built with ffmpeg from the 6 frames above (concat demuxer).
- Every frame carries a "DRAFT — NOT FINAL" badge. No voiceover yet (no TTS in this
  VM); the final cut needs a recorded voiceover from `DEMO_NARRATION.md`.
- Source frames: `docs/demo-frames/frame-1.png` … `frame-6.png` (1280×720 PNG).

## Final-cut shot list (what is still missing)

1. Real screen capture of the terminal for frames 2–4 (the draft uses text slides).
2. Real browser capture of the dashboard at http://localhost:8000 for frame 5.
3. Voiceover recording (English) from `DEMO_NARRATION.md`, ~3:30, mixed over the capture.
4. Optional: one `meko-test` take in real Meko mode (needs the free API key in `.env`).
5. Re-run `python -m quest_agent demo` from a clean state before recording so the
   progress goes 0/6 → 1/6 live on camera (the demo DB currently already shows
   1/6 done from the 2026-11-20 test run).
