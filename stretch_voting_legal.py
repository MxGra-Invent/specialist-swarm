"""
Stretch S9: voting pattern for contentious legal calls.

Creates three Legal Reviewer variants (conservative / balanced / aggressive),
each the normal Legal Reviewer prompt plus a stance paragraph, adds them to
the coordinator's roster, and tells the coordinator to send contentious
clauses to all three in parallel and synthesise a majority call.

Safe to re-run: only missing panelists are created, and the coordinator is
only updated if its roster or prompt lacks the panel.

Usage:
    python stretch_voting_legal.py
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from create_specialists import SPECIALISTS

load_dotenv(Path(__file__).resolve().parents[2] / "Basecamp-Exercises" / ".env")


VOTE_INSTRUCTION = (
    "\n\nEnd your reply with one line per clause you were asked about, "
    "in exactly this form:\n"
    "VOTE [<clause>]: ACCEPT | COUNTER | REJECT \u2014 <one-sentence rationale>\n"
    "(pick exactly one of the three votes per clause)."
)

STANCES = {
    "conservative": (
        "Your stance: CONSERVATIVE. Protect the firm first. Refuse anything "
        "that is off-checklist. You would rather lose the deal than sign "
        "terms that expose us."
    ),
    "balanced": (
        "Your stance: BALANCED. Follow the checklist. Be willing to trade "
        "concessions for value elsewhere in the deal."
    ),
    "aggressive": (
        "Your stance: AGGRESSIVE. Your goal is to win the deal. Accept risk "
        "where it is commercially justified, and look for creative contract "
        "structures that get to yes."
    ),
}

coordinator_addendum = """

# Legal voting panel

You have three extra Legal Reviewer panelists: Legal Reviewer (conservative),
Legal Reviewer (balanced) and Legal Reviewer (aggressive). The panel ADDS to
the four specialists; it does not replace them. Keep using the regular Legal
Reviewer for the full flag list.

This refines "delegate to ALL FOUR specialists in parallel": the four
contentious clauses known up front (MFN 3.4, termination for convenience 3.5,
uncapped breach liability 4.1, SLA termination) go to the three panelists IN
THE SAME fan-out message as the four specialists, so all 7 threads start
together. Send the SAME brief to all three panelists and do not tell any
panelist what the others think. Only blockers the Legal Reviewer surfaces
later trigger a second panel round, again with one message to all three.

Each panelist replies with one "VOTE [<clause>]: ..." line per clause.

Then synthesise a small table:
clause | conservative | balanced | aggressive | final call

Majority wins, but if the conservative panelist votes REJECT on a blocker,
you need an explicit written justification to override it. Record the split
in the proposal's "Contract approach" section.
"""


def build_panelists(legal_system: str, skill_id: str | None) -> list[dict]:
    """Return the kwargs for client.beta.agents.create, one per panelist."""
    panelists = []
    for stance, paragraph in STANCES.items():
        kwargs = dict(
            name=f"Legal Reviewer ({stance})",
            model="claude-sonnet-4-6",
            system=f"{legal_system}\n\n{paragraph}{VOTE_INSTRUCTION}",
            tools=[{"type": "agent_toolset_20260401"}],
            metadata={
                "hackathon": "partner-basecamp-2026",
                "track": "specialist-swarm",
                "role": f"legal_{stance}",
            },
        )
        if skill_id:
            kwargs["skills"] = [
                {"type": "custom", "skill_id": skill_id, "version": "latest"}
            ]
        panelists.append(kwargs)
    return panelists


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    coordinator_id = Path(".coordinator_id").read_text().strip()
    specialist_ids = json.loads(Path(".specialist_ids.json").read_text())

    keys = [f"legal_{stance}" for stance in STANCES]

    skill_ids_path = Path(".skill_ids.json")
    skill_ids = json.loads(skill_ids_path.read_text()) if skill_ids_path.exists() else {}
    skill_id = skill_ids.get("legal-checklist")

    legal = next(s for s in SPECIALISTS if s["key"] == "legal")

    client = Anthropic(
        api_key=api_key,
        default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
    )

    # Create only the missing panelists; persist after each so a crash can't orphan agents.
    for key, kwargs in zip(keys, build_panelists(legal["system"], skill_id)):
        if key in specialist_ids:
            continue
        agent = client.beta.agents.create(**kwargs)
        specialist_ids[key] = agent.id
        Path(".specialist_ids.json").write_text(json.dumps(specialist_ids, indent=2))
        print(f"  Created {kwargs['name']:34s} -> {agent.id}")

    # Coordinator idempotency is based on its actual state, not the json file.
    coordinator = client.beta.agents.retrieve(coordinator_id)
    roster = list(coordinator.multiagent.agents)
    have = {a["id"] if isinstance(a, dict) else a.id for a in roster}
    added = [specialist_ids[k] for k in keys if specialist_ids[k] not in have]
    roster += [{"type": "agent", "id": i} for i in added]
    system = coordinator.system
    if "# Legal voting panel" not in system:
        system += coordinator_addendum
    if not added and system == coordinator.system:
        print("Coordinator already has the voting panel; nothing to update.")
        return
    client.beta.agents.update(
        coordinator_id,
        version=coordinator.version,
        system=system,
        multiagent={"type": "coordinator", "agents": roster},
    )

    print("Coordinator roster updated. Now includes the legal voting panel.")
    print("Re-run run_deal_desk.py to see the vote in action.")


if __name__ == "__main__":
    main()
