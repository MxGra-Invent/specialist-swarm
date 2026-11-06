# Handoff — S9 Voting pattern

## What it is
For contentious contract clauses, three Legal Reviewer panelists (**conservative / balanced / aggressive**) get the same brief in parallel and each votes `ACCEPT | COUNTER | REJECT` on every clause. The coordinator puts the votes in a table and makes the final call. The majority wins, but overriding a conservative REJECT on a blocker needs a written justification. The split is recorded in the proposal's "Contract approach" section. This shows multi-agent used for *judgment*, not only for running tasks in parallel.

## Files (new, no existing files modified)
- `stretch_voting_legal.py`: creates the 3 panelists, adds them to the coordinator's roster and adds a `# Legal voting panel` section to the coordinator's system prompt.
- `test_stretch_voting_legal.py`: offline test with a fake client (`python test_stretch_voting_legal.py` prints `OK`).
- `outputs_before_s9/`: backup of `outputs/` from before the first S9 deal run. Can be deleted.

## How it works
- **Panelist prompts:** each one is the Legal Reviewer prompt imported from `create_specialists.SPECIALISTS`, plus a stance paragraph, plus an instruction to end with one line per clause: `VOTE [<clause>]: ACCEPT | COUNTER | REJECT — <rationale>`. Model `claude-sonnet-4-6`. The `legal-checklist` skill (from `.skill_ids.json`) is attached at creation.
- **Ids:** `.specialist_ids.json` gets the keys `legal_conservative`, `legal_balanced` and `legal_aggressive`.
- **Coordinator prompt addition:** the panel is *in addition to* the four specialists. The four contentious clauses known up front go to the panel in the **same fan-out message** as the four specialists, so 7 threads start at once. Those clauses are MFN §3.4, termination §3.5, uncapped breach liability §4.1 and SLA termination. A blocker the Legal Reviewer finds later triggers a second panel round.
- **Safe to rerun:** only missing panelist keys get created, and the ids file is saved after each create. Roster ids and the prompt section are only added if they're not already on the live coordinator, which is checked through `agents.retrieve`. If nothing changed, `agents.update` is skipped.

## Current live state (workspace, 2026-11-06)
- Coordinator `agent_01GXGZFYCJE5X2hHMMaVLrNE` **already has the panel**. Do not run `stretch_voting_legal.py` again unless the coordinator is recreated. If you do run it again, nothing happens.
- Panelists: conservative `agent_01VQxVpMuAWcLpJtF3BzGcWZ`, balanced `agent_01XtWp7yuECd89pmdN36AWom`, aggressive `agent_01NqrEdAvGGeQybY7GJnSPZy`.
- Critic (S2) is **not** on the roster yet (no `critic` key in `.specialist_ids.json`).

## Run
```bash
PY=/Users/max/00_code/anthropic_basecamp_sovai_key/.venv/bin/python
$PY stretch_voting_legal.py   # once, after create_coordinator.py
$PY run_deal_desk.py
```
Verified live on 2026-11-06: all 7 threads started together. 5 clauses were voted across 2 rounds (round 2 was a DPA/SCC blocker the Legal Reviewer found). Results: MFN and termination were unanimous COUNTERs. Liability, SLA and DPA were 2–1 COUNTERs that overrode the conservative REJECT with justifications. Produced `outputs/BTS-Synthetic_Proposal_Acme_Corp.docx` + `.md`. Session: https://platform.claude.com/sessions/sesn_01HvgkMSgMcGKpiBPAvEKmfv

## Integration notes for the merge / demo
- **Setup order when recreating agents:** `create_specialists.py` → `upload_skills.py` → `create_coordinator.py` → `stretch_voting_legal.py` (needs `.skill_ids.json` for the skill) → optionally `stretch_critic_subagent.py`. Both stretch scripts add to the roster and the system prompt, and they don't conflict.
- **`create_coordinator.py` creates a NEW coordinator** without the panel. Rerun `stretch_voting_legal.py` afterwards. It recreates nothing if the panelist ids are still in `.specialist_ids.json`, and only adds them to the new roster.
- **Deleting `.specialist_ids.json`** leads to 3 new panelists, and the old ones stay on any existing roster. Don't delete it.
- **S10 (recursion)** reads `outputs/BTS-Synthetic_Proposal_Acme_Corp.md`. This run produced it under that name. A bigger roster means more threads per recursion iteration.
- **Cost/time:** 7 sub-agents + an Opus coordinator. Do one warm-up run before the demo.
- **Known glitch (not fixed):** in round 2 the coordinator first sent the brief only to the conservative panelist, noticed, then sent it to the other two. The vote was complete, but it isn't a clean parallel start. The fix is one sentence in `coordinator_addendum` (e.g. "Every round, including follow-ups: all three panelists, in one message.") and then updating the live coordinator's system prompt. Because the rerun guard checks for the `# Legal voting panel` heading, rerunning the script will **not** apply an edited addendum. Patch it with `agents.update` or recreate the coordinator.
- **Demo talking point:** event stream → 3 `Legal Reviewer (…)` threads start next to the 4 specialists. Then show the coordinator's vote table: "three lawyers disagreed on uncapped liability; here's how the partner decided and why."
