"""Local web dashboard (stdlib http.server only, no dependencies).

Run:  python -m quest_agent serve [--port 8000]
Then open http://localhost:8000 — quests, progress, wallet address,
recent memories and decision traces, plus a chat box. All state lives in
the same SQLite store + Meko memory as the CLI, so the web UI and the CLI
share memory — the "shared memory" story in a browser.

JSON API:
    GET  /api/status   — progress, wallet, recent memories
    GET  /api/quests   — quest list with progress
    POST /api/step     — {"quest_id": "..."} complete next step
    POST /api/chat     — {"message": "..."} chat turn
    GET  /api/traces   — decision traces
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import agent as agent_mod
from . import config

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Quest Agent — ContextCon</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.4rem} .card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0}
button{padding:.4rem .8rem;margin:.2rem} input{padding:.4rem;width:70%}
.done{color:green}.todo{color:#888}</style></head><body>
<h1>Quest Agent — Airdrop quests with shared memory (Meko)</h1>
<p>ContextCon: Remember Everything · Theme: coding agents / agentic support</p>
<div class="card" id="status">Loading…</div>
<div class="card"><h2>Quests</h2><div id="quests">Loading…</div></div>
<div class="card"><h2>Chat with the agent</h2>
<input id="msg" placeholder="Ask what to do next…">
<button onclick="chat()">Send</button><pre id="answer"></pre></div>
<div class="card"><h2>Decision traces</h2><pre id="traces">Loading…</pre></div>
<script>
async function j(u,o){const r=await fetch(u,o);return r.json()}
async function load(){
 const s=await j('/api/status');
 document.getElementById('status').innerHTML =
  `<b>Memory mode:</b> ${s.mode} (datapack: ${s.meko_datapack})<br>`+
  `<b>Burner wallet:</b> ${s.wallet?s.wallet.address:'—'} (testnet only)<br>`+
  `<b>Progress:</b> ${s.progress.done}/${s.progress.total} quests, ${s.progress.points}/${s.progress.total_points} pts<br>`+
  `<b>Next:</b> ${s.next_quest?s.next_quest.title:'all done'}<br>`+
  `<b>Recent memories:</b><ul>${s.recent_memories.map(m=>'<li>['+m.source+'] '+m.text+'</li>').join('')}</ul>`;
 const qs=await j('/api/quests');
 document.getElementById('quests').innerHTML = qs.map(q=>
  `<div class="${q.status}"><b>${q.status==='done'?'[x]':q.status==='in_progress'?'[~]':'[ ]'} ${q.title}</b> (${q.chain})<br>${q.description}<br>`+
  q.steps.map((st,i)=>`${i<q.steps_done?'[x]':'[ ]'} ${st}`).join('<br>')+
  ` <button onclick="step('${q.id}')">Complete next step</button></div><hr>`).join('');
 const tr=await j('/api/traces');
 document.getElementById('traces').textContent = tr.map(t=>t.created_at+' — '+t.decision+' | '+t.reasoning).join('\\n');
}
async function step(id){await j('/api/step',{method:'POST',body:JSON.stringify({quest_id:id})});load()}
async function chat(){const m=document.getElementById('msg').value;
 const r=await j('/api/chat',{method:'POST',body:JSON.stringify({message:m})});
 document.getElementById('answer').textContent=r.answer;load()}
load();
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _agent(self):
        # Same pattern as the CLI: config values are bound at import time,
        # so re-read .env and reload the module or the server would report
        # "local" mode even with a key in .env (fixed 2026-11-21).
        config.load_dotenv()
        import importlib
        importlib.reload(config)
        return agent_mod.QuestAgent()

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self):
        if self.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        ag = self._agent()
        if self.path == "/api/status":
            self._send_json(ag.status())
        elif self.path == "/api/quests":
            self._send_json(ag.list_quests())
        elif self.path == "/api/traces":
            from . import store
            self._send_json(store.list_decision_traces(ag.conn))
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        ag = self._agent()
        data = self._read_json()
        if self.path == "/api/step":
            self._send_json(ag.complete_step(data.get("quest_id", "")))
        elif self.path == "/api/chat":
            self._send_json(ag.chat(data.get("message", "")))
        else:
            self._send_json({"error": "not found"}, status=404)


def serve(port=8000):
    config.load_dotenv()
    print(f"Quest Agent dashboard: http://localhost:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
