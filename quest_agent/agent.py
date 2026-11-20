"""QuestAgent — the orchestrator.

Flow for every user turn (the shared-memory loop that Meko enables):
1. Recall relevant memories from Meko (+ local mirror) for the query.
2. Decide what to do next (which quest, what step) and record that
   decision as a decision trace — Meko's "decision traces" concept,
   mirrored locally.
3. Act (list / start / complete a quest, remember a fact), then persist
   the outcome as a durable memory in Meko so the NEXT session — or
   another agent on the same datapack — picks up where this one stopped.

The agent never signs, broadcasts, or moves funds. Quest steps are
checklist items the user performs themselves, on testnet, with the
burner wallet.
"""
import uuid

from . import config, quests, store, wallet
from .memory import MemoryStore


class QuestAgent:
    def __init__(self, conn=None, memory=None, wallet_path=None):
        self.conn = conn or store.connect()
        self.memory = memory or MemoryStore.create(self.conn)
        self.wallet_path = wallet_path
        self.session_id = str(uuid.uuid4())[:8]

    # -- setup -------------------------------------------------------------
    def setup(self, wallet_path=None):
        """First-run setup: seed quests + burner wallet. Idempotent."""
        if wallet_path is not None:
            self.wallet_path = wallet_path
        n = quests.seed_quests(self.conn)
        info, created = wallet.ensure_burner_wallet(self.wallet_path)
        return {"seeded_quests": n, "wallet": info, "wallet_created": created}

    # -- status ------------------------------------------------------------
    def status(self):
        info = wallet.public_info(self.wallet_path)
        summary = quests.progress_summary(self.conn)
        nxt = quests.next_quest(self.conn)
        memories = store.list_memories(self.conn, limit=5)
        return {
            "mode": self.memory.mode,
            "meko_datapack": config.MEKO_DATAPACK_ID or "(default datapack)",
            "wallet": info,
            "progress": summary,
            "next_quest": (
                {"id": nxt["id"], "title": nxt["title"]} if nxt else None
            ),
            "recent_memories": [
                {"text": m["text"], "source": m["source"]} for m in memories
            ],
        }

    # -- quests ------------------------------------------------------------
    def list_quests(self):
        return store.list_quests(self.conn)

    def start_quest(self, quest_id):
        quest = store.get_quest(self.conn, quest_id)
        if quest is None:
            return {"ok": False, "error": f"Unknown quest: {quest_id}"}
        if quest["status"] == "done":
            return {"ok": False, "error": f"Quest {quest_id} is already done."}
        store.set_progress(self.conn, quest_id, "in_progress", quest["steps_done"])
        self._trace(
            f"Started quest {quest_id}",
            f"User started '{quest['title']}'. Next step: "
            f"{quest['steps'][quest['steps_done']]}.",
            [quest["title"]],
        )
        return {"ok": True, "quest": store.get_quest(self.conn, quest_id)}

    def complete_step(self, quest_id):
        quest = store.get_quest(self.conn, quest_id)
        if quest is None:
            return {"ok": False, "error": f"Unknown quest: {quest_id}"}
        if quest["status"] == "done":
            return {"ok": False, "error": f"Quest {quest_id} is already done."}
        steps_done = min(quest["steps_done"] + 1, len(quest["steps"]))
        status = "done" if steps_done >= len(quest["steps"]) else "in_progress"
        store.set_progress(self.conn, quest_id, status, steps_done)
        step_text = quest["steps"][steps_done - 1]
        if status == "done":
            fact = (
                f"User completed quest '{quest['title']}' ({quest_id}) "
                f"on {quest['chain']} with burner wallet "
                f"{wallet.public_info(self.wallet_path)['address']}. "
                f"Earned {quest['reward_points']} points."
            )
            saved = self.memory.remember(fact, metadata={"quest_id": quest_id})
            self._trace(
                f"Completed quest {quest_id}",
                f"All {len(quest['steps'])} steps done. Memory saved to "
                f"{'Meko' if saved['meko'] else 'local mirror only'}.",
                [fact],
            )
            return {"ok": True, "quest": store.get_quest(self.conn, quest_id),
                    "completed": True, "memory_saved_to_meko": saved["meko"]}
        self._trace(
            f"Completed step {steps_done}/{len(quest['steps'])} of {quest_id}",
            f"Step done: {step_text}.",
            [quest["title"]],
        )
        return {"ok": True, "quest": store.get_quest(self.conn, quest_id),
                "completed": False}

    # -- chat --------------------------------------------------------------
    def chat(self, message):
        """One conversational turn: recall -> decide -> answer -> persist."""
        memories = self.memory.recall(message, limit=5)
        memory_lines = [m["text"] for m in memories]
        nxt = quests.next_quest(self.conn)
        summary = quests.progress_summary(self.conn)
        if nxt:
            suggestion = (
                f"Next quest: {nxt['title']} ({nxt['id']}) — "
                f"{nxt['description']} Next step: {nxt['steps'][nxt['steps_done']]}."
            )
        else:
            suggestion = "All quests are done — nice work! Add a new quest to keep going."
        if memory_lines:
            recall_note = "I remember: " + " | ".join(memory_lines[:3])
        else:
            recall_note = "I don't have a relevant memory for that yet — I'll remember what you tell me."
        answer = (
            f"{recall_note}\n"
            f"Progress: {summary['done']}/{summary['total']} quests done, "
            f"{summary['points']}/{summary['total_points']} points.\n"
            f"{suggestion}"
        )
        self._trace(
            "Answered chat turn",
            f"Query: {message!r}. Used {len(memory_lines)} recalled memories. "
            f"Suggested: {nxt['id'] if nxt else 'none'}.",
            memory_lines,
        )
        self.memory.log_conversation(self.session_id, message, answer)
        return {"answer": answer, "memories_used": memory_lines,
                "next_quest": nxt["id"] if nxt else None}

    # -- helpers -----------------------------------------------------------
    def _trace(self, decision, reasoning, memory_used):
        store.add_decision_trace(self.conn, decision, reasoning, memory_used)
