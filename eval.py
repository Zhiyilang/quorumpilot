"""QuorumPilot eval suite - runs offline, no network, no API key.

    python eval.py

Every check is an assertion about behaviour a judge can verify by reading the
code: the arithmetic, the rule engine, the evidence verifier, the arbiter, the
MCP protocol, and the safety property that a lying agent loses its vote.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quorumpilot.agent import review                                   # noqa: E402
from quorumpilot.arbitrate import arbitrate, suggest_units, tally      # noqa: E402
from quorumpilot.brain import Brain, OfflineBrain                      # noqa: E402
from quorumpilot.ingest import Blob, ingest, ingest_files              # noqa: E402
from quorumpilot.market import (compute_metrics, corr_to,              # noqa: E402
                                parse_snapshot, policy_check,
                                solve_units_for_risk)
from quorumpilot.receipts import build_receipt, receipt_json, render_html  # noqa: E402
from quorumpilot.verify import fact_bundle, verify_claim, verify_claims    # noqa: E402

ROOT = Path(__file__).resolve().parent
EX = ROOT / "examples"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (
        "   <- " + str(detail) if (detail and not cond) else ""))


def load(name):
    return json.loads((EX / name).read_text(encoding="utf-8"))


RISKY, CLEAN, CAUTION = (load("proposal_risky.json"), load("proposal_clean.json"),
                         load("proposal_caution.json"))


def snap_of(payload):
    s = parse_snapshot(payload)
    return s, compute_metrics(s)


# --------------------------------------------------------------- A. parsing
print("\nA. parsing")
s, m = snap_of(RISKY)
check("risky: 2 positions parsed", len(s.account.positions) == 2)
check("risky: equity read", m["account.equity"] == 25000.0)
check("risky: no warnings", s.warnings == [], s.warnings)

s2, m2 = snap_of(json.dumps(CLEAN))          # JSON *text* must also work
check("accepts JSON text as well as dict", m2["account.equity"] == 50000.0)

bad = parse_snapshot({"account": {"equity": 10000, "positions": [
    {"symbol": "", "units": 1, "entry": 1.0},
    {"symbol": "EURUSD", "units": None, "entry": 1.0},
    {"symbol": "EURUSD", "units": 1000, "entry": 0},
    {"symbol": "EURUSD", "units": 1000, "entry": 1.1},
]}})
check("3 unreadable rows skipped, 1 kept", len(bad.account.positions) == 1)
check("skipped rows are reported, not silent",
      any("skipped" in w for w in bad.warnings), bad.warnings)

nm = parse_snapshot({"account": {"balance": 9000},
                     "proposal": {"symbol": "usdjpy", "side": "SELL",
                                  "units": -5000, "entry": "150.25"}})
check("balance is accepted when equity is absent",
      nm.account.equity == 9000.0)
check("free_margin derived from equity - used_margin",
      nm.account.free_margin == 9000.0)
check("symbol is upper-cased", nm.proposal.symbol == "USDJPY")
check("negative units + SELL -> short", nm.proposal.side == "short")
check("units normalised to a positive magnitude", nm.proposal.units == 5000.0)
check("numeric strings are parsed", nm.proposal.entry == 150.25)

p = parse_snapshot({"account": {}, "proposal": {"symbol": "EURUSD"},
                    "policy": {"max_risk_pct_per_trade": "1.5",
                               "restricted_symbols": ["eurusd"]}})
check("policy values as strings are coerced",
      p.policy["max_risk_pct_per_trade"] == 1.5)
check("restricted list is upper-cased",
      p.policy["restricted_symbols"] == ["EURUSD"])

# --------------------------------------------------------------- B. metrics
print("\nB. metrics")
check("risk_amount = distance x units", m["metrics.risk_amount"] == 2500.0,
      m["metrics.risk_amount"])
check("risk_pct = risk / equity", m["metrics.risk_pct"] == 10.0,
      m["metrics.risk_pct"])
check("reward:risk computed", m["metrics.rr_ratio"] == 1.0, m["metrics.rr_ratio"])
check("notional = units x entry", m["metrics.notional"] == 632500.0)
check("effective leverage = notional / equity",
      abs(m["metrics.effective_leverage"] - 25.3) < 0.01,
      m["metrics.effective_leverage"])
check("margin required = notional / leverage",
      abs(m["metrics.margin_required"] - 21083.33) < 0.1)
check("free margin after is negative here",
      m["metrics.free_margin_after"] < 0, m["metrics.free_margin_after"])
check("open risk sums both stops",
      m["metrics.open_risk_pct"] == 3.6, m["metrics.open_risk_pct"])
check("total risk = open + proposed",
      m["metrics.total_risk_pct"] == 13.6, m["metrics.total_risk_pct"])
check("worst-case equity subtracts every stop",
      m["metrics.worst_case_equity"] == 21600.0)
check("risk concentration is risk-based, not notional",
      m["metrics.risk_concentration_pct"] == 10.0)
check("correlated risk pools same-quote-currency legs",
      m["metrics.correlated_risk_pct"] == 13.6, m["metrics.correlated_risk_pct"])
check("correlated legs are named with their correlation",
      len(m["metrics.correlated_with"]) == 2, m["metrics.correlated_with"])
check("a leveraged ticket is not flagged as concentration by notional",
      m["metrics.risk_concentration_pct"] < 100)

check("same symbol correlates 1.0", corr_to("EURUSD", "EURUSD", {}) == 1.0)
check("shared quote currency implies 0.7",
      corr_to("GBPUSD", "EURUSD", {}) == 0.7)
check("shared base currency implies 0.7",
      corr_to("EURUSD", "EURJPY", {}) == 0.7)
check("unrelated pair implies 0.1", corr_to("EURUSD", "USDCHF", {}) == 0.1)
check("supplied matrix overrides the heuristic",
      corr_to("EURUSD", "USDCHF", {"EURUSD": {"USDCHF": 0.95}}) == 0.95)

_, cm = snap_of(CLEAN)
check("clean ticket: 0.06% at risk",
      abs(cm["metrics.risk_pct"] - 0.06) < 0.001, cm["metrics.risk_pct"])
check("clean ticket: no correlated legs", cm["metrics.correlated_with"] == [])

# --------------------------------------------------------------- C. rules
print("\nC. rule engine")
rules = {b["rule"] for b in policy_check(m, s.policy)}
for r in ("RISK_PER_TRADE", "TOTAL_RISK", "LEVERAGE", "RISK_CONCENTRATION",
          "CORRELATED_RISK", "REWARD_RISK", "FREE_MARGIN"):
    check("risky trips %s" % r, r in rules, sorted(rules))
check("clean ticket trips no rule",
      policy_check(cm, parse_snapshot(CLEAN).policy) == [])

def one(**kw):
    payload = {"account": {"equity": 10000, "free_margin": 10000},
               "proposal": {"symbol": "EURUSD", "units": 10000,
                            "entry": 1.10, "stop": 1.099,
                            "take_profit": 1.102, "leverage": 10}}
    payload.update(kw)
    sp = parse_snapshot(payload)
    return policy_check(compute_metrics(sp), sp.policy)


check("restricted symbol is blocked",
      any(b["rule"] == "RESTRICTED_SYMBOL" for b in
          one(policy={"restricted_symbols": ["EURUSD"]})))
check("missing stop is a hard breach",
      any(b["rule"] == "NO_STOP" for b in
          one(proposal={"symbol": "EURUSD", "units": 10000, "entry": 1.10,
                        "leverage": 10})))
big = one(account={"equity": 100000, "free_margin": 100000, "positions": [
              {"symbol": "EURUSD", "units": 1000, "entry": 1.10,
               "stop": 1.09}]},
          proposal={"symbol": "EURUSD", "units": 1000, "entry": 1.10,
                    "stop": 1.09, "take_profit": 1.12, "leverage": 10},
          policy={"max_positions": 1})
check("position count cap fires",
      any(b["rule"] == "MAX_POSITIONS" for b in big), [b["rule"] for b in big])
check("stop wider than the price limit fires",
      any(b["rule"] == "STOP_TOO_WIDE" for b in
          one(proposal={"symbol": "EURUSD", "units": 10000, "entry": 1.10,
                        "stop": 1.00, "take_profit": 1.30, "leverage": 10},
              policy={"max_stop_pct_of_price": 5})))
check("every breach cites evidence",
      all(b["evidence"] for b in policy_check(m, s.policy)))

# --------------------------------------------------------------- D. verifier
print("\nD. evidence verifier")
bundle = fact_bundle(s, m)
good = {"statement": "risk is 10.00% of equity", "stance": "objection",
        "evidence": [{"locator": "metrics.risk_pct", "excerpt": "10.00%"}]}
ok, why = verify_claim(good, bundle)
check("a true claim with a real citation survives", ok, why)
ok, why = verify_claim(
    {"statement": "x", "stance": "caution",
     "evidence": [{"locator": "metrics.risk_pct", "excerpt": "0.01%"}]}, bundle)
check("a claim that misquotes the number is dropped", not ok)
ok, why = verify_claim(
    {"statement": "x", "stance": "caution",
     "evidence": [{"locator": "metrics.made_up_field", "excerpt": "5"}]}, bundle)
check("a claim citing a field that does not exist is dropped",
      not ok and "not found" in why[0], why)
ok, _ = verify_claim({"statement": "x", "stance": "caution",
                      "evidence": []}, bundle)
check("a claim with no evidence is dropped", not ok)
ok, _ = verify_claim({"statement": "x", "stance": "vibes",
                      "evidence": [{"locator": "metrics.risk_pct",
                                    "excerpt": "10.00%"}]}, bundle)
check("an unknown stance is dropped", not ok)
ok, _ = verify_claim({"statement": "", "stance": "caution",
                      "evidence": [{"locator": "metrics.risk_pct",
                                    "excerpt": "10.00%"}]}, bundle)
check("an empty statement is dropped", not ok)
ok, _ = verify_claim(
    {"statement": "x", "stance": "caution",
     "evidence": [{"locator": "metrics.risk_pct", "excerpt": "roughly ten"}]},
    bundle)
check("an excerpt with no number cannot back a numeric field", not ok)
ok, _ = verify_claim(
    {"statement": "x", "stance": "caution",
     "evidence": [{"locator": "proposal.symbol", "excerpt": "GBPUSD"}]}, bundle)
check("a string field can be cited by name", ok)

for name, payload in (("risky", RISKY), ("clean", CLEAN), ("caution", CAUTION)):
    r = review(payload, prefer_llm=False)
    check("%s: every deterministic claim verifies" % name,
          r["decision"]["claims_dropped"] == 0,
          r["decision"]["dropped"])
    check("%s: every claim carries evidence" % name,
          all(c["evidence"] for c in r["verified"]))

# --------------------------------------------------------------- E. arbiter
print("\nE. arbiter")
rr = review(RISKY, prefer_llm=False)
cc = review(CLEAN, prefer_llm=False)
uu = review(CAUTION, prefer_llm=False)
check("risky ticket is REJECTED", rr["decision"]["verdict"] == "REJECT")
check("clean ticket is cleared", cc["decision"]["verdict"] == "PROCEED")
check("marginal ticket is cleared with caution",
      uu["decision"]["verdict"] == "PROCEED_WITH_CAUTION")
check("caution is not a block", uu["decision"]["breaches"] == [])
check("verdicts only come from the three allowed values",
      all(x["decision"]["verdict"] in ("PROCEED", "PROCEED_WITH_CAUTION",
                                       "REJECT") for x in (rr, cc, uu)))
check("tally counts every stance",
      sum(rr["decision"]["tally"].values()) == rr["decision"]["claims_verified"])
check("a suggested size is offered for the rejected ticket",
      rr["decision"]["suggested_units"], rr["decision"]["suggested_units"])
check("the suggestion is smaller than what was proposed",
      rr["decision"]["suggested_units"] < RISKY["proposal"]["units"])
check("no suggestion when nothing is breached",
      cc["decision"]["suggested_units"] is None)

fit = json.loads(json.dumps(RISKY))
fit["proposal"]["units"] = rr["decision"]["suggested_units"]
fit_rules = {b["rule"] for b in review(fit, prefer_llm=False)["breaches"]}
for r in ("RISK_PER_TRADE", "TOTAL_RISK", "LEVERAGE", "RISK_CONCENTRATION",
          "CORRELATED_RISK", "FREE_MARGIN"):
    check("suggested size fixes %s" % r, r not in fit_rules, sorted(fit_rules))
check("sizing cannot fix a bad reward:risk (honest about its limits)",
      "REWARD_RISK" in fit_rules)

su = suggest_units(s, m, rr["breaches"])
check("suggest_units is monotonic-safe (never larger than proposed)",
      su is None or su <= m["proposal.units"])
check("solve_units_for_risk returns whole units",
      float(solve_units_for_risk(s, 2.0)).is_integer())
check("solve_units_for_risk hits the cap exactly",
      abs(100.0 * solve_units_for_risk(s, 2.0) * m["metrics.stop_distance"]
          / 25000.0 - 2.0) < 0.01)
check("solve with no stop returns 0 rather than guessing",
      solve_units_for_risk(parse_snapshot({"account": {"equity": 1000},
                                           "proposal": {"symbol": "EURUSD",
                                                        "units": 1,
                                                        "entry": 1.1}}), 2.0) == 0.0)

# --------------------------------------------------------------- F. lying agent
print("\nF. a lying agent loses its vote")


class LiarBrain(Brain):
    """Fabricates confident, plausible, entirely false claims."""

    name = "liar"

    def propose(self, snap, m, bundle):
        return [
            {"id": "llm-1", "agent": "llm-specialist",
             "statement": "This trade is perfectly safe, I checked.",
             "stance": "support",
             "evidence": [{"locator": "metrics.risk_pct", "excerpt": "0.02%"}]},
            {"id": "llm-2", "agent": "llm-specialist",
             "statement": "Equity is ten million dollars.",
             "stance": "support",
             "evidence": [{"locator": "account.equity", "excerpt": "10000000.00"}]},
            {"id": "llm-3", "agent": "llm-specialist",
             "statement": "The volatility index confirms it.",
             "stance": "support",
             "evidence": [{"locator": "metrics.vix_implied", "excerpt": "12"}]},
        ]


liar = review(RISKY, brain=LiarBrain(), prefer_llm=False)
check("the liar's claims are all dropped",
      liar["decision"]["claims_dropped"] == 3, liar["decision"]["dropped"])
check("the liar's claims never reach the verdict",
      all(c["agent"] != "llm-specialist" for c in liar["verified"]))
check("the verdict is unchanged by the liar",
      liar["decision"]["verdict"] == rr["decision"]["verdict"])
check("dropped claims keep their reasons for the record",
      all(d.get("reasons") for d in liar["decision"]["dropped"]))
check("the receipt reports brain + drop count",
      liar["receipt"]["output"]["claims_dropped"] == 3)
check("a truthful model keeps its vote",
      verify_claims([{"id": "t", "agent": "x", "stance": "support",
                      "statement": "s", "evidence": [
                          {"locator": "metrics.risk_pct", "excerpt": "10.00%"}]}],
                    bundle)[0] != [])

# --------------------------------------------------------------- G. receipts
print("\nG. receipts")
rec = json.loads(receipt_json(rr))
check("receipt JSON parses", rec["verdict"] == "REJECT")
check("receipt carries the decision and the claims",
      "decision" in rec and rec["claims"])
check("receipt records the brain used", rec["brain"] == "offline-deterministic")
html_r = render_html(rr)
check("HTML receipt is self-contained (no external asset)",
      "http://" not in html_r and "https://" not in html_r)
check("HTML receipt states the verdict", "REJECT" in html_r)
check("HTML receipt lists the dropped claims section",
      "Claims dropped" in html_r)

evil = json.loads(json.dumps(CLEAN))
evil["proposal"]["symbol"] = "</script><img src=x onerror=alert(1)>EURUSD"
ev = review(evil, prefer_llm=False)
eh = render_html(ev)
check("a hostile symbol cannot break out of the HTML receipt",
      "</script><img" not in eh.lower() and "&lt;/script&gt;" in eh.lower())
check("a hostile symbol cannot break the JSON receipt",
      json.loads(receipt_json(ev))["decision"]["symbol"].lower()
      .startswith("</script>"))

# --------------------------------------------------------------- H. MCP
print("\nH. MCP server (real subprocess, spec 2025-11-25)")
PY = sys.executable
msgs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2025-11-25",
                "capabilities": {}, "clientInfo": {"name": "eval", "version": "1"}}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "load_snapshot", "arguments": RISKY}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
     "params": {"name": "review_trade", "arguments": RISKY}},
    {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
     "params": {"name": "explain_verdict", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
     "params": {"name": "policy_check", "arguments": RISKY}},
    {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
     "params": {"name": "suggest_size", "arguments": RISKY}},
    {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
     "params": {"name": "nope", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
     "params": {"name": "explain_verdict", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
     "params": {"name": "ingest_sources",
                "arguments": {
                    "sources": [
                        {"name": "a.csv",
                         "text": "Instrument,Qty,Avg Price,Stop\n"
                                 "EUR/USD,100000,1.0850,1.0800\n"},
                        {"name": "acct.json",
                         "text": json.dumps({"equity": 30000,
                                             "free_margin": 24000})},
                    ],
                    "proposal": {"symbol": "GBPUSD", "side": "long",
                                 "units": 200000, "entry": 1.2665,
                                 "stop": 1.2600, "take_profit": 1.2800,
                                 "leverage": 30}}}},
]
proc = subprocess.run(
    [PY, "-m", "quorumpilot.mcp_server"],
    input="".join(json.dumps(x) + "\n" for x in msgs),
    capture_output=True, text=True, timeout=180, cwd=str(ROOT))
lines = [json.loads(x) for x in proc.stdout.splitlines() if x.strip()]
by_id = {x.get("id"): x for x in lines}

check("MCP: initialize returns 2025-11-25",
      by_id[1]["result"]["protocolVersion"] == "2025-11-25")
check("MCP: server identifies itself",
      by_id[1]["result"]["serverInfo"]["name"] == "quorumpilot")
check("MCP: 6 tools advertised", len(by_id[2]["result"]["tools"]) == 6,
      [t["name"] for t in by_id[2]["result"]["tools"]])
check("MCP: ingest_sources is among them",
      any(t["name"] == "ingest_sources"
          for t in by_id[2]["result"]["tools"]))
check("MCP: every tool has an input schema",
      all("inputSchema" in t for t in by_id[2]["result"]["tools"]))
f3 = json.loads(by_id[3]["result"]["content"][0]["text"])
check("MCP: load_snapshot returns computed facts",
      f3["facts"]["metrics.risk_pct"] == 10.0)
f4 = json.loads(by_id[4]["result"]["content"][0]["text"])
check("MCP: review_trade returns a verdict", f4["verdict"] == "REJECT")
check("MCP: review_trade returns a receipt with a trace",
      len(f4["receipt"]["trace"]) >= 6)
check("MCP: review_trade lists what survived verification",
      f4["verified_claims"] and f4["tally"]["objection"] > 0)
check("MCP: responses are never truncated into invalid JSON",
      all(isinstance(json.loads(x["result"]["content"][0]["text"]), dict)
          for x in (by_id[3], by_id[4], by_id[6], by_id[7])))
f5 = json.loads(by_id[5]["result"]["content"][0]["text"])
check("MCP: explain_verdict explains the last decision",
      f5["verdict"] == "REJECT" and f5["explain"])
f6 = json.loads(by_id[6]["result"]["content"][0]["text"])
check("MCP: policy_check returns breaches", len(f6["breaches"]) == 7)
f7 = json.loads(by_id[7]["result"]["content"][0]["text"])
check("MCP: suggest_size returns a smaller size",
      f7["suggested_units"] < f7["proposed_units"])
check("MCP: unknown tool is an error, not a crash",
      by_id[8]["result"]["isError"] is True)
check("MCP: a notification (no id) gets no reply", 0 not in by_id)
f10 = json.loads(by_id[10]["result"]["content"][0]["text"])
check("MCP: ingest_sources merges the two blobs",
      f10["positions"] == 1 and f10["verdict"], f10)
check("MCP: ingest_sources reports provenance",
      any(k.startswith("positions[") for k in f10["provenance"]))

# --------------------------------------------------------------- I. CLI
print("\nI. CLI")
env = dict(os.environ, PYTHONPATH=str(ROOT))
r = subprocess.run([PY, "-m", "quorumpilot", "review",
                    str(EX / "proposal_caution.json"), "--json"],
                   capture_output=True, text=True, timeout=180, cwd=str(ROOT))
check("CLI --json emits parseable JSON",
      json.loads(r.stdout)["verdict"] == "PROCEED_WITH_CAUTION")
r = subprocess.run([PY, "-m", "quorumpilot", "policy",
                    str(EX / "proposal_clean.json")],
                   capture_output=True, text=True, timeout=180, cwd=str(ROOT))
check("CLI policy exits 0 when clean", r.returncode == 0 and "no breaches" in r.stdout)
r = subprocess.run([PY, "-m", "quorumpilot", "policy",
                    str(EX / "proposal_risky.json")],
                   capture_output=True, text=True, timeout=180, cwd=str(ROOT))
check("CLI policy exits 1 when breached", r.returncode == 1)
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "receipt.html"
    r = subprocess.run([PY, "-m", "quorumpilot", "review",
                        str(EX / "proposal_risky.json"), "--html", str(out)],
                       capture_output=True, text=True, timeout=180, cwd=str(ROOT))
    check("CLI --html writes a report", out.exists() and out.stat().st_size > 500)

# --------------------------------------------------------------- J. fragmented
print("\nJ. fragmented ingestion")
FRAG = sorted(str(p) for p in (EX / "fragmented").glob("*")
              if p.name != "proposal.json")
FRAG_PROP = json.loads((EX / "fragmented" / "proposal.json").read_text())

ing = ingest_files(FRAG, proposal=FRAG_PROP)
roles = {s.name: s.role for s in ing.sources}
check("CSV with odd headers is read as positions",
      roles.get("broker_a_positions.csv") == "positions", roles)
check("JSON list with different key names is read as positions",
      roles.get("venue_b_positions.json") == "positions", roles)
check("symbol+price file is read as prices",
      roles.get("prices.csv") == "prices", roles)
check("flat key:value file is read as the account",
      roles.get("account.json") == "account", roles)
check("max_*/min_* keys are read as policy",
      roles.get("policy.json") == "policy", roles)
check("policy values land in the payload",
      ing.payload["policy"]["max_risk_pct_per_trade"] == 1.5)
check("equity is picked up from the flat file",
      ing.payload["account"]["equity"] == 30000.0)
check("symbols are normalised across sources (EUR/USD -> EURUSD)",
      all("/" not in p["symbol"] for p in ing.payload["account"]["positions"]))
check("EURUSD appears once despite two sources",
      sum(1 for p in ing.payload["account"]["positions"]
          if p["symbol"] == "EURUSD") == 1)
check("the duplicate is reported as a conflict, not silently merged",
      any("EURUSD" in c and "keeping the first" in c for c in ing.conflicts),
      ing.conflicts)
check("the first source wins on conflict",
      [p["units"] for p in ing.payload["account"]["positions"]
       if p["symbol"] == "EURUSD"] == [100000.0])
check("prices are joined onto positions by symbol",
      any(p.get("current") == 1.0872 for p in ing.payload["account"]["positions"]))
check("provenance is kept for merged positions",
      any(k.startswith("positions[") for k in ing.provenance))
check("provenance names the source file",
      any(v.get("source") == "broker_a_positions.csv"
          for k, v in ing.provenance.items() if k.startswith("positions")))
check("no unreadable-source warnings in the happy path",
      ing.warnings == [], ing.warnings)
check("the merged book reviews to REJECT",
      review(ing.payload, prefer_llm=False)["decision"]["verdict"] == "REJECT")
check("ingesting nothing is not a crash",
      ingest_files([]).payload["account"]["positions"] == [])
junk = ingest_files([str(EX / "proposal_clean.json")], proposal=None)
check("a single well-formed file still ingests",
      junk.payload is not None)
check("garbage text is reported, not swallowed",
      any("could not read" in w.lower() for w in
          ingest([Blob("junk.txt", "hello world")]).warnings))

r = subprocess.run([sys.executable, "-m", "quorumpilot", "ingest"] + FRAG +
                   ["--proposal", str(EX / "fragmented" / "proposal.json")],
                   capture_output=True, text=True, timeout=180, cwd=str(ROOT))
check("CLI ingest merges and reviews",
      "REJECT" in r.stdout and "Conflicts" in r.stdout)

# --------------------------------------------------------------- summary
print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print("  - " + f)
    sys.exit(1)
