"""Zero-dependency web demo for QuorumPilot.

Same core as the CLI, the MCP server and the Gradio app - this file only
serves. Standard library only, so it runs anywhere Python runs (Render,
WorkBuddy, a laptop) with nothing to install.

Routes:
  GET  /               single-page demo (reckless example pre-run)
  GET  /healthz        liveness probe
  POST /api/review     body = proposal JSON -> full receipt JSON
  GET  /api/demo/<n>   n in {reckless, clean, marginal} -> receipt JSON

Environment:
  PORT  listen port (default 8080)
  HOST  bind host  (default 0.0.0.0, as PaaS expect)
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from quorumpilot.agent import review
from quorumpilot.receipts import receipt_json

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
DEMOS = {
    "reckless": "proposal_risky.json",
    "clean": "proposal_clean.json",
    "marginal": "proposal_caution.json",
}

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuorumPilot - live quorum demo</title>
<style>
  :root{ --bg:#0e1116; --panel:#161b22; --ink:#e6edf3; --muted:#9da7b3; --line:#2a313a;
         --accent:#58a6ff; --good:#3fb950; --bad:#f85149; --warn:#d29922; }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:15px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  .wrap{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
  .kicker{color:var(--accent);font-weight:600;letter-spacing:.08em;text-transform:uppercase;
           font-size:12px;margin-bottom:10px}
  h1{font-size:34px;margin:0 0 6px}
  .sub{color:var(--muted);font-style:italic;margin-bottom:22px}
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media (max-width:900px){ .cols{grid-template-columns:1fr} }
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
  .card h2{margin:0 0 10px;font-size:15px;color:var(--accent)}
  textarea{width:100%;height:300px;background:#0b0e13;color:var(--ink);border:1px solid var(--line);
           border-radius:8px;padding:12px;font-family:ui-monospace,Consolas,monospace;
           font-size:12.5px;resize:vertical}
  .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
  button{cursor:pointer;border-radius:8px;border:1px solid var(--line);background:#1c2330;
         color:var(--ink);padding:8px 14px;font-size:13.5px}
  button:hover{border-color:var(--accent)}
  button.primary{background:#1f6feb;border-color:#1f6feb;color:#fff}
  .verdict{font-size:26px;font-weight:800;letter-spacing:.02em}
  .ok{color:var(--good)} .warn{color:var(--warn)} .bad{color:var(--bad)}
  .meta{color:var(--muted);font-size:13px;margin-top:4px}
  .term{background:#0b0e13;border:1px solid var(--line);border-radius:8px;padding:12px 14px;
        font-family:ui-monospace,Consolas,monospace;font-size:12.5px;white-space:pre-wrap;
        margin-top:10px;max-height:340px;overflow:auto}
  .foot{color:var(--muted);font-size:12.5px;margin-top:26px}
  .tag{display:inline-block;background:#1f6feb22;border:1px solid #1f6feb55;color:var(--accent);
       border-radius:999px;padding:2px 10px;font-size:12px;margin:0 6px 6px 0}
</style>
</head>
<body>
<div class="wrap">
  <div class="kicker">Deriv &middot; Rise of AI Agents &mdash; Collaborative Systems track</div>
  <h1>QuorumPilot</h1>
  <div class="sub">A model may speak. It may not be believed. &mdash; live, running the real engine.</div>
  <div>
    <span class="tag">multi-agent</span><span class="tag">deterministic verifier</span>
    <span class="tag">cited evidence</span><span class="tag">offline</span><span class="tag">MCP 2025-11-25</span>
  </div>

  <div class="cols" style="margin-top:18px">
    <div class="card">
      <h2>proposal (editable JSON)</h2>
      <textarea id="payload" spellcheck="false"></textarea>
      <div class="row">
        <button class="primary" onclick="run(document.getElementById('payload').value)">Run the quorum</button>
        <button onclick="load('reckless')">Reckless</button>
        <button onclick="load('clean')">Clean</button>
        <button onclick="load('marginal')">Marginal</button>
      </div>
    </div>
    <div class="card">
      <h2>verdict</h2>
      <div id="out"><div class="meta">running&hellip;</div></div>
    </div>
  </div>

  <div class="foot">
    The four specialist agents propose; a deterministic verifier decides which claims count;
    a pure-arithmetic arbiter decides the verdict. No model touches the final number.<br>
    MIT &middot; zero dependencies &middot; 137 offline assertions &middot; github.com/Zhiyilang/quorumpilot
  </div>
</div>
<script>
function cls(v){ return v==='PROCEED'?'ok':(v==='PROCEED_WITH_CAUTION'?'warn':'bad'); }
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function show(r){
  var d=r.decision, m=r.metrics, o=document.getElementById('out');
  var html='<div class="verdict '+cls(d.verdict)+'">'+d.verdict.replace(/_/g,' ')+'</div>'
    +'<div class="meta">score '+d.score+' &middot; brain='+esc(r.brain)
    +(r.brain_degraded?' (degraded)':'')+' &middot; '+r.duration_ms+' ms</div>'
    +'<div class="meta">'+d.side+' '+d.symbol+' '+Math.round(m['proposal.units'])+' units'
    +' &middot; risk '+d.risk_pct.toFixed(2)+'% of equity ('+m['account.currency']+' '
    +d.risk_amount.toFixed(2)+')</div>'
    +'<div class="meta">claims: '+d.claims_verified+' verified, '+d.claims_dropped+' dropped</div>';
  if(d.breaches && d.breaches.length){
    html+='<div class="term">breaches:\\n';
    d.breaches.forEach(function(b){ html+='  - '+esc(b.rule)+': '+esc(b.detail)+'\\n'; });
    html+='</div>';
  }
  html+='<div class="term">'+esc(d.explain)+'</div>';
  if(d.suggested_units){ html+='<div class="meta">-&gt; fit the rules at '+Math.round(d.suggested_units)+' units</div>'; }
  o.innerHTML=html;
}
function run(text){
  var payload;
  try{ payload=JSON.parse(text); }catch(e){ alert('invalid JSON: '+e.message); return; }
  fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},
                       body:JSON.stringify(payload)})
    .then(function(r){ return r.json().then(function(j){ if(!r.ok) throw new Error(j.error||r.status); return j; }); })
    .then(show)
    .catch(function(e){ document.getElementById('out').innerHTML='<div class="meta bad">'+e.message+'</div>'; });
}
function load(name){
  fetch('/api/demo/'+name).then(function(r){ return r.json(); }).then(function(j){
    document.getElementById('payload').value=JSON.stringify(j.payload||j,null,2);
    fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},
                         body:JSON.stringify(j.payload||j)})
      .then(function(r){ return r.json(); }).then(show);
  });
}
fetch('/api/demo/reckless').then(function(r){ return r.json(); }).then(function(j){
  document.getElementById('payload').value=JSON.stringify(j.payload,null,2);
  show(j);
});
</script>
</body>
</html>
"""


def _run_review(payload):
    """Run the quorum offline-deterministic. Returns (status, receipt_dict)."""
    try:
        result = review(payload, prefer_llm=False)
    except Exception as exc:  # never leak a stack to the browser
        return 500, {"error": "%s: %s" % (type(exc).__name__, exc)}
    return 200, json.loads(receipt_json(result))


class Handler(BaseHTTPRequestHandler):
    server_version = "QuorumPilotDemo/1.0"

    def _send(self, status, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/healthz":
            self._send(200, json.dumps({"code": 200, "msg": "Health Checked",
                                        "data": "Pod alive"}))
        elif path.startswith("/api/demo/"):
            name = path[len("/api/demo/"):]
            if name not in DEMOS:
                self._send(404, json.dumps({"error": "unknown demo: %s" % name}))
                return
            try:
                payload = json.loads((EXAMPLES / DEMOS[name]).read_text(encoding="utf-8"))
            except Exception as exc:
                self._send(500, json.dumps({"error": str(exc)}))
                return
            status, receipt = _run_review(payload)
            if isinstance(receipt, dict):
                receipt = dict(receipt)
                receipt["payload"] = payload
            self._send(status, json.dumps(receipt))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/review":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        raw = self.rfile.read(n) if n > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self._send(400, json.dumps({"error": "invalid JSON: %s" % exc}))
            return
        if isinstance(payload, dict) and "payload" in payload:
            payload = payload["payload"]
        status, receipt = _run_review(payload)
        self._send(status, json.dumps(receipt))

    def log_message(self, fmt, *args):  # keep PaaS logs quiet but useful
        pass


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("PORT", "8080"))
    except ValueError:
        port = 8080
    httpd = ThreadingHTTPServer((host, port), Handler)
    print("QuorumPilot demo on http://%s:%d  (offline-deterministic)" % (host, port))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
