"""Minimal Meko MCP client (stdlib only, JSON-RPC over Streamable HTTP).

Implements the official Meko Cloud integration from
https://docs.mekodata.ai/use-meko/connect/ and
https://docs.mekodata.ai/reference/mcp-server/ :

* Endpoint: ``https://mcp.mekodata.ai/mcp`` (same for every account/datapack)
* Auth: ``Authorization: Bearer <mko_tkn_...>`` + ``User-Agent`` header.
  Meko rejects requests without either header.
* The ``datapack_id`` in each tool call selects the datapack (one datapack
  per project). Tools used here: ``datapack_list``, ``memory_add``,
  ``memory_search``, ``context_search``, ``conversation_create``,
  ``conversation_add_message``, ``knowledgebase_upload_document``.

No API key is bundled. Without ``MEKO_API_KEY`` the client raises
``MekoNotConfigured`` and callers fall back to the local memory mirror —
the app still runs end-to-end for a local demo.
"""
import json
import urllib.error
import urllib.request

from . import config

USER_AGENT = "meko-mcp-installer/1.0"


class MekoError(Exception):
    """Base error for Meko failures."""


class MekoNotConfigured(MekoError):
    """No MEKO_API_KEY set — Meko Cloud is unavailable."""


class MekoAuthError(MekoError):
    """401 from Meko — the API key is invalid/expired/revoked."""


class MekoUnavailable(MekoError):
    """Network or server error talking to the Meko MCP endpoint."""


class MekoClient:
    """Thin JSON-RPC client for the Meko MCP server (Streamable HTTP)."""

    def __init__(self, api_key=None, datapack_id=None, url=None, timeout=None):
        self.api_key = api_key if api_key is not None else config.MEKO_API_KEY
        self.datapack_id = datapack_id if datapack_id is not None else config.MEKO_DATAPACK_ID
        self.url = url or config.MEKO_MCP_URL
        self.timeout = timeout or config.MEKO_TIMEOUT_S
        self._session_id = None
        self._next_id = 1
        self._initialized = False
        self._conversation_id = None

    def ensure_conversation(self, title="quest-agent session"):
        """Lazily create one Meko conversation for this client and reuse it.

        Meko MCP server v3.2.4 scopes the memory/datapack tools to a
        conversation: every call needs ``conversation_id`` (verified
        2026-11-21 — datapack_list/memory_add without one fail validation).
        """
        if self._conversation_id:
            return self._conversation_id
        out = self.call_tool("conversation_create", {
            "agent_id": config.MEKO_AGENT_ID,
            "title": title,
        })
        try:
            parsed = json.loads(out)
            cid = parsed.get("conversation_id") or parsed.get("id")
        except (ValueError, TypeError):
            cid = None
        if not cid:
            raise MekoError("could not create a Meko conversation")
        self._conversation_id = cid
        return cid

    # -- transport ---------------------------------------------------------
    def _post(self, payload, extra_headers=None):
        if not self.api_key:
            raise MekoNotConfigured(
                "MEKO_API_KEY is not set. Create a free Meko account at "
                "https://cloud.mekodata.ai, generate an API key in "
                "Settings > API Keys, and put it in .env (see .env.example)."
            )
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        if extra_headers:
            headers.update(extra_headers)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                session = resp.headers.get("Mcp-Session-Id")
                if session:
                    self._session_id = session
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise MekoAuthError(
                    "Meko returned 401: API key invalid, expired, or revoked. "
                    "Generate a new key in the Meko portal (Settings > API Keys)."
                ) from exc
            raise MekoUnavailable(f"Meko MCP endpoint returned HTTP {exc.code}") from exc
        except Exception as exc:  # network error, timeout, proxy error, ...
            raise MekoUnavailable(f"Could not reach Meko MCP endpoint: {exc}") from exc
        return self._parse_response(raw)

    @staticmethod
    def _parse_response(raw):
        """Parse a Streamable HTTP response (JSON or SSE `data:` lines)."""
        raw = raw.strip()
        if not raw:
            return None
        if raw.startswith("{"):
            return json.loads(raw)
        result = None
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data = line[5:].strip()
                if data and data != "[DONE]":
                    result = json.loads(data)
        return result

    def _rpc(self, method, params=None):
        payload = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        self._next_id += 1
        if params is not None:
            payload["params"] = params
        resp = self._post(payload)
        if isinstance(resp, dict) and "error" in resp:
            raise MekoError(f"Meko MCP error for {method}: {resp['error']}")
        return resp

    # -- MCP lifecycle -----------------------------------------------------
    def initialize(self):
        """MCP initialize handshake. Returns the server result dict."""
        if self._initialized:
            return True
        resp = self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "contextcon-quest-agent", "version": "0.1.0"},
        })
        # Notification: initialized (no response expected; ignore failures).
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except MekoError:
            pass
        self._initialized = True
        return resp.get("result", {}) if isinstance(resp, dict) else {}

    def call_tool(self, name, arguments):
        """Call one Meko MCP tool by name. Returns the tool result content."""
        self.initialize()
        resp = self._rpc("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        result = resp.get("result", {}) if isinstance(resp, dict) else {}
        content = result.get("content", [])
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
        if result.get("isError"):
            raise MekoError(f"Meko tool {name} failed: {' '.join(texts)}")
        return "\n".join(texts)

    def list_tools(self):
        self.initialize()
        resp = self._rpc("tools/list")
        result = resp.get("result", {}) if isinstance(resp, dict) else {}
        return [t.get("name") for t in result.get("tools", [])]

    # -- Meko tools used by this project -----------------------------------
    def _base_args(self, extra=None):
        # Conversation-scoped: the server rejects agent_id on the memory /
        # datapack tools and requires conversation_id (see ensure_conversation).
        # An explicit conversation_id in `extra` wins over the cached one.
        args = {"conversation_id": self.ensure_conversation()}
        if self.datapack_id:
            args["datapack_id"] = self.datapack_id
        if extra:
            args.update(extra)
        return args

    def datapack_list(self):
        out = self.call_tool("datapack_list", self._base_args())
        try:
            return json.loads(out)
        except (ValueError, TypeError):
            return {"raw": out}

    def memory_add(self, text, metadata=None):
        args = self._base_args({"text": text})
        if metadata:
            args["metadata"] = metadata
        return self.call_tool("memory_add", args)

    def memory_search(self, query, limit=5):
        out = self.call_tool("memory_search", self._base_args({"query": query, "limit": limit}))
        try:
            return json.loads(out)
        except (ValueError, TypeError):
            return {"raw": out}

    def context_search(self, query, limit=5):
        out = self.call_tool("context_search", self._base_args({"query": query, "limit": limit}))
        try:
            return json.loads(out)
        except (ValueError, TypeError):
            return {"raw": out}

    def conversation_create(self, title, session_id=None):
        # Built directly, NOT via _base_args: _base_args itself creates a
        # conversation, so routing through it here would spawn a spare one.
        # agent_id is accepted on this tool (unlike the memory tools).
        args = {"agent_id": config.MEKO_AGENT_ID, "title": title}
        if session_id:
            args["session_id"] = session_id
        out = self.call_tool("conversation_create", args)
        try:
            return json.loads(out)
        except (ValueError, TypeError):
            return {"raw": out}

    def conversation_add_message(self, conversation_id, user_input, assistant_output, plan=None):
        args = self._base_args({
            "conversation_id": conversation_id,
            "input": user_input,
            "output": assistant_output,
        })
        if plan:
            args["plan"] = plan
        return self.call_tool("conversation_add_message", args)
