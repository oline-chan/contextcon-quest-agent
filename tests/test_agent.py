import tempfile
import unittest
from pathlib import Path

from quest_agent.agent import QuestAgent
from quest_agent.memory import MemoryStore
from quest_agent.store import connect


class TestQuestAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.conn = connect(self.db)
        # Local-only memory (no MEKO_API_KEY in this environment).
        self.agent = QuestAgent(conn=self.conn, memory=MemoryStore(self.conn, meko=None))
        # Temp wallet path: tests must never touch the real data/ wallet.
        self.wallet_path = Path(self.tmp.name) / "burner_wallet.json"
        self.agent.setup(wallet_path=self.wallet_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seed_and_status(self):
        status = self.agent.status()
        self.assertEqual(status["progress"]["total"], 6)
        self.assertEqual(status["progress"]["done"], 0)
        self.assertEqual(status["mode"], "local")
        self.assertTrue(status["wallet"]["address"].startswith("0x"))

    def test_complete_quest_remembers_it(self):
        # Status must report the temp test wallet, never the real one.
        from quest_agent.wallet import public_info
        self.assertEqual(
            public_info(self.wallet_path)["address"],
            self.agent.status()["wallet"]["address"],
        )
        self.agent.start_quest("quest-daily-checkin")
        for _ in range(7):
            out = self.agent.complete_step("quest-daily-checkin")
        self.assertTrue(out["completed"])
        self.assertFalse(out["memory_saved_to_meko"])  # no key -> local only
        # A fresh agent instance (new session) recalls the completion.
        fresh = QuestAgent(conn=connect(self.db),
                           memory=MemoryStore(connect(self.db), meko=None))
        hits = fresh.memory.recall("daily check-in quest")
        self.assertTrue(any("daily check-in" in h["text"].lower() for h in hits))

    def test_chat_suggests_next_quest(self):
        reply = self.agent.chat("What should I do next?")
        self.assertIn("Next quest", reply["answer"])
        self.assertIsNotNone(reply["next_quest"])

    def test_unknown_quest(self):
        self.assertFalse(self.agent.start_quest("nope")["ok"])
        self.assertFalse(self.agent.complete_step("nope")["ok"])

    def test_decision_traces_recorded(self):
        self.agent.chat("hello")
        from quest_agent.store import list_decision_traces
        self.assertGreaterEqual(len(list_decision_traces(self.conn)), 1)


if __name__ == "__main__":
    unittest.main()
