"""Offline test for stretch_recursion.py. Run: python test_stretch_recursion.py"""

import contextlib
import io
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ["ANTHROPIC_API_KEY"] = "test-key"

import stretch_recursion as m  # noqa: E402

# ---- parse_decision ----
assert m.parse_decision("blah\nNEXT QUESTION: Is the SLA realistic?") == ("next", "Is the SLA realistic?")
assert m.parse_decision("blah\nSTOP: risk is acceptable") == ("stop", "risk is acceptable")
assert m.parse_decision("x\n   **next question:** Is pricing right?  \n") == ("next", "Is pricing right?")
assert m.parse_decision("**STOP: all good**") == ("stop", "all good")
assert m.parse_decision("NEXT QUESTION: a\nSTOP: b") == ("stop", "b")  # last wins
assert m.parse_decision("STOP: a\nNEXT QUESTION: b\nnotes") == ("next", "b")
assert m.parse_decision("no decision here") == ("stop", "no decision line")
assert m.parse_decision("") == ("stop", "no decision line")
assert m.parse_decision("NEXT QUESTION:   ") == ("stop", "no decision line")  # empty question


# ---- fake client ----
class FakeClient:
    def __init__(self, reply_fn):
        self.reply_fn = reply_fn  # (iteration_index, prompt) -> reply text
        self.created, self.prompts, self.replies = [], {}, {}
        sessions = SimpleNamespace(
            create=self._create,
            events=SimpleNamespace(stream=self._stream, send=self._send),
        )
        self.beta = SimpleNamespace(sessions=sessions)

    def _create(self, **kw):
        self.created.append(kw)
        return SimpleNamespace(id=f"sess_{len(self.created)}")

    def _send(self, session_id, events):
        self.prompts[session_id] = events[0]["content"][0]["text"]

    @contextlib.contextmanager
    def _stream(self, session_id):
        def gen():
            idx = int(session_id.split("_")[1]) - 1
            text = self.reply_fn(idx, self.prompts[session_id])
            self.replies[session_id] = text
            yield SimpleNamespace(type="session.thread_created", agent_name="Legal Reviewer")
            # coordinator often emits several messages; the last one carries the decision
            *body, last = text.split("\n")
            yield SimpleNamespace(type="agent.message", content=[SimpleNamespace(type="text", text="\n".join(body))])
            yield SimpleNamespace(type="agent.message", content=[SimpleNamespace(type="text", text=last)])
            yield SimpleNamespace(type="session.status_idle")
        yield gen()


def run(reply_fn, argv, tmp):
    client = FakeClient(reply_fn)
    m.Anthropic = lambda: client
    with contextlib.redirect_stdout(io.StringIO()) as out:
        m.main(argv)
    return client, out.getvalue(), (Path(tmp) / "outputs" / "recursion-log.md").read_text()


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    m.HERE = root
    (root / ".coordinator_id").write_text("coord_1\n")
    (root / ".environment_id").write_text("env_1\n")
    (root / "synthetic-data").mkdir()
    (root / "outputs").mkdir()
    (root / "synthetic-data/rfp-acme-corp.md").write_text("RFP BODY")
    (root / "outputs/BTS-Synthetic_Proposal_Acme_Corp.md").write_text("PROPOSAL BODY")
    (root / "outputs/coordinator-transcript.txt").write_text("TRANSCRIPT BODY")

    # STOP on iteration 2
    def stop_at_2(i, prompt):
        return "Finding 1.\nNEXT QUESTION: Can we staff it?" if i == 0 else "Finding 2.\nSTOP: acceptable"

    c, out, log = run(stop_at_2, [], tmp)
    assert len(c.created) == 2, len(c.created)
    assert all(k["agent"] == "coord_1" and k["environment_id"] == "env_1" for k in c.created)
    assert [r for r in c.prompts] == ["sess_1", "sess_2"]  # a new session per iteration
    p1, p2 = c.prompts["sess_1"], c.prompts["sess_2"]
    assert m.FIRST_QUESTION in p1 and "Do NOT produce a docx" in p1
    for doc in ("RFP BODY", "PROPOSAL BODY", "TRANSCRIPT BODY"):
        assert doc in p1 and doc in p2
    assert "Can we staff it?" in p2
    assert m.FIRST_QUESTION in p2 and "Finding 1." in p2  # earlier question + findings
    assert "Finding 1." not in p1
    assert "Iteration 1" in log and "Iteration 2" in log
    assert "Finding 1." in log and "Finding 2." in log and "Can we staff it?" in log
    assert "https://platform.claude.com/sessions/sess_1" in log
    assert "https://platform.claude.com/sessions/sess_2" in log
    assert "Stopped: STOP: acceptable" in out

    # cap hit at --max 2 when the model always says NEXT
    c, out, log = run(lambda i, p: f"Finding {i}.\nNEXT QUESTION: Q{i + 2}?", ["--max", "2"], tmp)
    assert len(c.created) == 2
    assert "Iteration 1" in log and "Iteration 2" in log and "Iteration 3" not in log
    assert "iteration cap (2) hit" in out and "Q3?" in out
    # log is overwritten per run (above two runs: no iteration-1 duplicates)
    assert log.count("## Iteration 1") == 1

    # unparseable reply stops after 1
    c, out, log = run(lambda i, p: "rambling without a decision", ["--max", "5"], tmp)
    assert len(c.created) == 1
    assert "no decision line" in out and "Iteration 2" not in log

    # default cap is 3
    c, _, _ = run(lambda i, p: "x\nNEXT QUESTION: more?", [], tmp)
    assert len(c.created) == 3

    # missing context file -> SystemExit
    (root / "outputs/coordinator-transcript.txt").unlink()
    try:
        run(lambda i, p: "", [], tmp)
        raise AssertionError("expected SystemExit")
    except SystemExit as e:
        assert "coordinator-transcript.txt" in str(e)

print("OK")
