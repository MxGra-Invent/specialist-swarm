"""Offline test for stretch_voting_legal.py. Run: python test_stretch_voting_legal.py"""

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ["ANTHROPIC_API_KEY"] = "test-key"

import stretch_voting_legal as m  # noqa: E402
from create_specialists import SPECIALISTS  # noqa: E402

LEGAL = next(s for s in SPECIALISTS if s["key"] == "legal")["system"]


class FakeAgents:
    def __init__(self):
        self.created, self.updates = [], []
        self.coord_system = "COORD PROMPT"
        self.coord_roster = [{"type": "agent", "id": "agent_old"}]

    def create(self, **kw):
        self.created.append(kw)
        return SimpleNamespace(id=f"agent_new_{len(self.created)}")

    def retrieve(self, _id):
        return SimpleNamespace(
            version=7,
            system=self.coord_system,
            multiagent=SimpleNamespace(agents=list(self.coord_roster)),
        )

    def update(self, agent_id, **kw):
        self.updates.append((agent_id, kw))
        self.coord_system = kw["system"]
        self.coord_roster = kw["multiagent"]["agents"]


agents = FakeAgents()
m.Anthropic = lambda **kw: SimpleNamespace(beta=SimpleNamespace(agents=agents))

with tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)
    Path(".coordinator_id").write_text("coord_1\n")
    Path(".specialist_ids.json").write_text(json.dumps({"legal": "agent_old"}))
    Path(".skill_ids.json").write_text(json.dumps({"legal-checklist": "skill_legal"}))

    m.main()

    assert len(agents.created) == 3
    systems = [c["system"] for c in agents.created]
    assert len(set(systems)) == 3
    for stance, c in zip(["CONSERVATIVE", "BALANCED", "AGGRESSIVE"], agents.created):
        assert LEGAL in c["system"]
        assert stance in c["system"]
        assert "VOTE [<clause>]: ACCEPT | COUNTER | REJECT" in c["system"]
        assert c["model"] == "claude-sonnet-4-6"
        assert c["skills"] == [
            {"type": "custom", "skill_id": "skill_legal", "version": "latest"}
        ]

    assert len(agents.updates) == 1
    coord_id, kw = agents.updates[0]
    assert coord_id == "coord_1" and kw["version"] == 7
    assert [a["id"] for a in kw["multiagent"]["agents"]] == [
        "agent_old", "agent_new_1", "agent_new_2", "agent_new_3",
    ]
    assert kw["system"] == "COORD PROMPT" + m.coordinator_addendum
    assert kw["system"].count("# Legal voting panel") == 1
    assert "ALL FOUR specialists" in kw["system"] and "7 threads" in kw["system"]

    ids = json.loads(Path(".specialist_ids.json").read_text())
    assert ids["legal"] == "agent_old"
    assert [ids[k] for k in ("legal_conservative", "legal_balanced", "legal_aggressive")] == [
        "agent_new_1", "agent_new_2", "agent_new_3",
    ]

    # second run: no duplicates, no update call
    m.main()
    assert len(agents.created) == 3 and len(agents.updates) == 1

    # partial state: only legal_balanced present, coordinator untouched -> creates exactly 2
    agents.created.clear(); agents.updates.clear()
    agents.coord_system = "COORD PROMPT"
    agents.coord_roster = [{"type": "agent", "id": "agent_old"}]
    Path(".specialist_ids.json").write_text(
        json.dumps({"legal": "agent_old", "legal_balanced": "agent_pre"})
    )
    m.main()
    assert len(agents.created) == 2
    ids = json.loads(Path(".specialist_ids.json").read_text())
    assert ids["legal_balanced"] == "agent_pre" and len(ids) == 4
    roster = [a["id"] for a in agents.updates[0][1]["multiagent"]["agents"]]
    assert len(roster) == len(set(roster)) == 4 and "agent_pre" in roster
    assert agents.updates[0][1]["system"].count("# Legal voting panel") == 1

    # no skills file -> no skills kwarg
    assert all("skills" not in p for p in m.build_panelists(LEGAL, None))

print("OK")
