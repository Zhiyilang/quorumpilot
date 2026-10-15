# Submission checklist — two competitions, one project

## Competition 1 — The Rise of AI Agents Hackathon (lablab.ai / Dubai AI Week)

**Prize pool:** $60,000+ · **Build window:** 26 Oct – 2 Nov 2026 · **Finale (invite only, Dubai):** 3–7 Nov
**Tracks:** 🤝 Collaborative Systems (primary), 🔄 Agentic Workflows (secondary)
**Eligibility:** global, online participation, solo or team, 18+. Confirmed from the official lablab.ai event page.

## Competition 2 — Open Agent Hackathon 2026 (GenAI Works)

**Prize pool:** up to $20,000 · **Build window:** 22–27 Oct 2026 · **Registration closes:** 22 Oct 23:59 UTC
**Track:** 01 — Solving Fragmented Intelligence (discover and work across fragmented data sources)
**Eligibility:** fully online, 16+, solo or teams of 1–5. Free entry.

The `ingest` layer exists exactly for this track: five mismatched venue exports
(CSV with odd headers, JSON with different key names, price file, flat account
object, policy object) merged into one book with provenance and conflict
reporting. Publishing on **26 Oct** sits inside *both* build windows.

> **Order of operations:** register for Open Agent **before 22 Oct** (that is a
> user action — the form needs an email), then publish on the 26th.

## Why one project can honestly enter both

| Requirement | Deriv / lablab | Open Agent | QuorumPilot |
|---|---|---|---|
| Original work built in the window | yes | yes | repo created 26 Oct, inside both |
| Multi-agent / collaborative | Collaborative Systems track | "agentic applications" | 4 specialists + arbiter |
| Tool use / workflows | Agentic Workflows track | multi-step reasoning | 6 MCP tools, 6-stage loop |
| Fragmented data | — | track 01 | `ingest.py` + provenance |
| Works without paid APIs | yes | yes | stdlib only, no key needed |

Neither ruleset forbids dual submission. Check each form's own checkbox on the
day; if either asks for exclusivity, Deriv ($60k) takes priority.

## Do not do these before 26 Oct

- [ ] **Do not create the public repo / Space before the build window opens.** lablab hackathons expect work built inside the window. Keep the code local until 26 Oct.
- [ ] Do not publish the DEV/HF/Reddit post before the window opens.

## 26 Oct — opening day (do all of this the same day)

- [ ] Register on **lablab.ai** (this is also the account needed for the Vultr Agent Rush submission — one registration covers both).
- [ ] Create the public repo `Zhiyilang/quorumpilot`, MIT, push everything in this folder.
- [ ] Deploy: Render (`render.yaml`) **and/or** a Hugging Face Space. Put the live URL in the README and in the submission.
- [ ] Run `python eval.py` on a clean clone and paste the result (`137 passed, 0 failed`) into the README.
- [ ] Post a short build log / thread with the repo link.
- [ ] Submit the same project to **Open Agent** (window closes 27 Oct) — track 01, Solving Fragmented Intelligence.

## 26 Oct – 1 Nov — optional upgrades, in priority order

1. **Add the LLM member with Gemini** (tracks require Gemini for Google GCP prizes):
   `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai`, `OPENAI_MODEL=gemini-3-flash`.
   No code change — `brain.py` already speaks OpenAI-compatible. Record one run showing a hallucinated claim being dropped.
2. **Vultr** is a partner: if the Vultr key is available by then, deploy there too and mention it.
3. Add a second correlated-pair example with a real correlation matrix.

## 1–2 Nov — submission

- [ ] Record the demo (≤3 min) following `DEMO_SCRIPT.md`, upload unlisted→public on YouTube.
- [ ] Fill the lablab submission form:

**Title:** QuorumPilot — an agent quorum where unprovable claims lose their vote

**Tagline:** Four specialist agents review a trade; a deterministic verifier throws out every claim they can't prove.

**Description (paste):** see `README.md` "Why this exists" + "The four specialists" + "Honest limits".

**Track:** Collaborative Systems

**Built with:** Python (stdlib only), MCP, Gradio, optional Gemini via OpenAI-compatible API

**Links:** repo · live demo · video

- [ ] Re-read the official rules page once more on submission day — lablab sometimes adds a required field.

## What the judges will actually check

| They ask | Where the answer is |
|---|---|
| Is it an *agent*, not a prompt? | `agents.py` — 4 specialists propose; `arbitrate.py` decides |
| Does it do multi-step work? | PERCEIVE→SPECIALIZE→VERIFY→ARBITRATE→EXPLAIN→RECEIPT, `agent.py` |
| Does it use tools? | 5 MCP tools, `mcp_server.py`, protocol `2025-11-25` |
| Is it novel? | The verifier: claims without provable evidence lose their vote (eval §F) |
| Does it work without a key? | Yes — the whole quorum is deterministic |
| Is it honest about limits? | `DESIGN.md` "What was cut" + README "Honest limits" |

## Notes on eligibility (verified 15 Oct 2026)

- Online participation is open globally; the Dubai finale is invite-only and travel is **not** covered. Nothing in the rules requires travel to win.
- On-site attendance is by invitation; do not book anything.
- Google GCP prizes specifically require Gemini models — covered by step 1 above.
