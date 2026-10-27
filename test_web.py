"""Offline checks for the web demo layer (web.py).

Self-contained: starts its own server on an ephemeral free port (or uses
QP_WEB_BASE if you point it at a deployed instance, e.g.
QP_WEB_BASE=https://clauseguard-ai.app.workbuddy.host python test_web.py).

Stdlib only. Exits non-zero on the first failed contract.

Two environment traps this file is built to survive:
  1. a sandbox/VPN HTTP_PROXY that intercepts even 127.0.0.1 -> 502
     (fixed with an explicit no-proxy opener);
  2. a hardcoded port that happens to be busy -> "binds" via SO_REUSEADDR
     but connections reach the squatter (fixed with bind(("",0))).
"""

import json
import os
import socket
import sys
import threading
import urllib.request

BASE = os.environ.get("QP_WEB_BASE")
_server = None
if not BASE:
    import web as _web  # noqa: E402  (same directory, run from repo root)

    def _free_port():
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    _server = _web.ThreadingHTTPServer(("127.0.0.1", _free_port()), _web.Handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    BASE = "http://127.0.0.1:%d" % _server.server_address[1]

# never let a proxy env var hijack loopback traffic
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

FAILED = []


def check(name, cond, detail=""):
    print("%-42s %s %s" % (name, "PASS" if cond else "FAIL", detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def get(path):
    with _opener.open(BASE + path, timeout=20) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with _opener.open(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    with _opener.open(BASE + "/", timeout=20) as r:
        page = r.read().decode("utf-8")
    check("GET / is 200 HTML", r.status == 200 and "QuorumPilot" in page)

    st, h = get("/healthz")
    check("GET /healthz 200 + code 200", st == 200 and h.get("code") == 200)

    st, r = get("/api/demo/reckless")
    d = r["decision"]
    check("reckless -> REJECT", d["verdict"] == "REJECT", d["verdict"])
    check("reckless score=-55", d["score"] == -55, str(d["score"]))
    check("reckless 7 breaches", len(d["breaches"]) == 7, str(len(d["breaches"])))
    check("reckless 16 verified / 0 dropped",
          d["claims_verified"] == 16 and d["claims_dropped"] == 0,
          "%d/%d" % (d["claims_verified"], d["claims_dropped"]))
    check("reckless brain offline-deterministic",
          r["brain"] == "offline-deterministic", str(r["brain"]))
    check("reckless echo carries payload", "payload" in r and
          r["payload"]["proposal"]["symbol"] == "GBPUSD")

    st, r = get("/api/demo/clean")
    check("clean -> PROCEED", r["decision"]["verdict"] == "PROCEED",
          r["decision"]["verdict"])

    st, r = get("/api/demo/marginal")
    check("marginal -> PROCEED_WITH_CAUTION",
          r["decision"]["verdict"] == "PROCEED_WITH_CAUTION",
          r["decision"]["verdict"])

    st, r = post("/api/review", json.loads(
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "examples", "proposal_clean.json"),
             encoding="utf-8").read()))
    check("POST /api/review -> PROCEED", st == 200 and
          r["decision"]["verdict"] == "PROCEED", "%s %s" % (st, r.get("decision")))

    st, r = post("/api/review", {"nonsense": True})
    # The engine is built for honest zero-results: a payload with no account
    # data must not crash - it degrades to a provable REJECT (no stop, no
    # margin) with a full trace, not a 500 and not a fabricated verdict.
    check("junk payload -> graceful receipt, no crash",
          st == 200 and r["decision"]["verdict"] == "REJECT"
          and r["decision"]["claims_dropped"] == 0
          and len(r["trace"]) >= 8, "%s %s" % (st, r.get("decision")))

    req = urllib.request.Request(BASE + "/api/review", data=b"not json",
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        _opener.open(req, timeout=20)
        st = 200
    except urllib.error.HTTPError as e:
        st = e.code
    check("POST invalid JSON -> 400", st == 400, str(st))

    try:
        _opener.open(BASE + "/nope", timeout=20)
        st = 200
    except urllib.error.HTTPError as e:
        st = e.code
    check("GET unknown path -> 404", st == 404, str(st))

    print("-" * 60)
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("ALL WEB-LAYER CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
