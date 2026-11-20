"""Unified memory: Meko Cloud first, local SQLite mirror always.

This is the heart of the ContextCon entry (Use of Meko = 30% of the score):

* ``remember(text)`` — writes to Meko via the ``memory_add`` MCP tool
  (durable fact in the project's datapack, shared across agents/users),
  then mirrors the same text locally. If Meko is not configured or the
  call fails, the local mirror still stores it and the caller is told
  the write was local-only — nothing is silently lost, nothing is faked.
* ``recall(query)`` — searches Meko first (``memory_search``, then
  ``context_search`` for open-ended recall across memory + knowledge base
  + conversations), then merges in local keyword hits, de-duplicated.
* ``log_conversation(...)`` — saves a turn to Meko
  (``conversation_create`` once per session, then
  ``conversation_add_message``) and mirrors it locally. Meko extracts
  durable facts from saved turns asynchronously.

Without a Meko API key the app runs in local-demo mode and says so
explicitly in its output — the demo never pretends a Meko write happened.
"""
from . import config, meko_client, store


class MemoryStore:
    def __init__(self, conn, meko=None):
        self.conn = conn
        self.meko = meko  # MekoClient or None
        self._conversation_id = None

    @classmethod
    def create(cls, conn):
        meko = None
        if config.meko_configured():
            try:
                meko = meko_client.MekoClient()
                meko.initialize()
            except meko_client.MekoError:
                meko = None  # fall back to local-only; caller reports it
        return cls(conn, meko)

    @property
    def mode(self):
        return "meko" if self.meko is not None else "local"

    def remember(self, text, metadata=None):
        """Store a durable fact. Returns {'meko': bool, 'local_id': int}."""
        meko_ok = False
        if self.meko is not None:
            try:
                self.meko.memory_add(text, metadata=metadata)
                meko_ok = True
            except meko_client.MekoError:
                meko_ok = False
        local_id = store.add_memory(
            self.conn, text,
            source="meko" if meko_ok else "local",
            metadata=metadata,
        )
        return {"meko": meko_ok, "local_id": local_id}

    def recall(self, query, limit=5):
        """Search memory. Returns a list of {'text', 'source'} dicts."""
        results = []
        seen = set()
        if self.meko is not None:
            for tool in ("memory_search", "context_search"):
                try:
                    out = getattr(self.meko, tool)(query, limit=limit)
                    for item in self._extract_texts(out):
                        if item not in seen:
                            seen.add(item)
                            results.append({"text": item, "source": f"meko:{tool}"})
                except meko_client.MekoError:
                    continue
        for row in store.search_memories_local(self.conn, query, limit=limit):
            if row["text"] not in seen:
                seen.add(row["text"])
                results.append({"text": row["text"], "source": "local"})
        return results[:limit]

    @staticmethod
    def _extract_texts(payload):
        """Pull plain text out of the many shapes Meko tool results take."""
        texts = []
        if isinstance(payload, str):
            texts.append(payload)
            return texts
        if isinstance(payload, dict):
            for key in ("results", "memories", "items"):
                if isinstance(payload.get(key), list):
                    for item in payload[key]:
                        texts.extend(MemoryStore._extract_texts(item))
            for key in ("text", "content", "memory", "summary"):
                if isinstance(payload.get(key), str):
                    texts.append(payload[key])
        return [t for t in texts if t.strip()]

    def log_conversation(self, session_id, user_input, assistant_output):
        """Save a turn (Meko conversation + local mirror)."""
        meko_conv = None
        if self.meko is not None:
            try:
                if self._conversation_id is None:
                    created = self.meko.conversation_create(
                        title=f"Quest agent session {session_id}", session_id=session_id
                    )
                    if isinstance(created, dict):
                        self._conversation_id = (
                            created.get("conversation_id") or created.get("id")
                        )
                if self._conversation_id:
                    self.meko.conversation_add_message(
                        self._conversation_id, user_input, assistant_output
                    )
                    meko_conv = self._conversation_id
            except meko_client.MekoError:
                meko_conv = None
        return store.add_conversation(
            self.conn, session_id, user_input, assistant_output,
            meko_conversation_id=meko_conv,
        )
