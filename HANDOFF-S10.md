# Handoff — S10 Recursion pattern

## What it is
After the proposal exists, the coordinator asks itself "What's the riskiest assumption in this proposal?" A **new session** investigates that question. Its reply ends with either `NEXT QUESTION: …` (the loop runs again with that question) or `STOP: …` (the loop ends). `--max N` is a hard cap on iterations and acts as the spend cap.

## Files (new, self-contained, no existing files modified)
- `stretch_recursion.py`: the loop.
- `test_stretch_recursion.py`: offline test with a fake client (`python test_stretch_recursion.py` prints `OK`).
- Output: `outputs/recursion-log.md` is overwritten each run. It holds one section per iteration: the question, the full reply and the session link.

## How it works
- **Context:** `synthetic-data/rfp-acme-corp.md`, `outputs/BTS-Synthetic_Proposal_Acme_Corp.md` and `outputs/coordinator-transcript.txt` (see `CONTEXT_FILES`). All must exist, so run `run_deal_desk.py` first.
- **Agents:** it uses the existing coordinator (`.coordinator_id`) and environment (`.environment_id`). It creates no new agents and changes no rosters.
- **Prompt rules:** reflection only, no docx or files, and delegate only to the specialists the question needs. This overrides the coordinator's default "fan out to all and produce a docx" from its system prompt.
- **Stopping:** `parse_decision()` reads the last `NEXT QUESTION:` / `STOP:` line. If there is no decision line or the question is empty, it stops (safe default).
- **Prompts after the first** include all earlier questions and findings so the coordinator doesn't repeat itself.

## Run
```bash
/Users/max/00_code/anthropic_basecamp_sovai_key/.venv/bin/python stretch_recursion.py --max 3
```
Verified live on 2026-11-06 with `--max 1`, about 2–3 min per iteration. The coordinator delegated only to Pricing and Competitive Intel. It found the riskiest assumption to be that our 28% discount survives RFP §3.3's 35% floor, and returned a valid NEXT QUESTION. Session: https://platform.claude.com/sessions/sesn_01FTCzZM1y46mxiTBgFwJQfg

## Integration notes for the merge / demo
- **Order:** setup scripts → `run_deal_desk.py` (makes the proposal) → `stretch_recursion.py`. The deck (`run_deck_live.py`) is independent and can run before or after.
- **If the proposal filename changes** (the docx skill sometimes names files differently), update `CONTEXT_FILES` in `stretch_recursion.py`.
- **Roster:** the loop works with whatever roster the coordinator has (voting panel S9, critic S2, …). The prompt limits delegation, but a bigger roster can still mean more threads per iteration. Lower `--max` if time is tight.
- **Demo talking point:** the terminal shows `=== ITERATION i ===`, the specialists each iteration picks, the findings, then the next self-generated question. The final SUMMARY lists the question chain and why it stopped (STOP vs. cap).
- **Possible extension (not built):** feed `recursion-log.md` back into the proposal or the deck as a "Risk deep-dive" section by adding it to `run_deck_live.py`'s `CONTEXT_FILES`.
- **Known cosmetic issue:** thread event lines like `[thread spawned]` print on the same line as the coordinator's narration.
