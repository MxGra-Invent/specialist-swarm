"""
Stretch S10: recursion pattern.

After the proposal exists, the coordinator asks itself "What's the riskiest
assumption in this proposal?", a NEW session investigates it (delegating only to
the relevant specialists), and the reply ends with either
`NEXT QUESTION: ...` (loop again) or `STOP: ...` (remaining risk acceptable).
`--max N` is the hard cap on iterations (= the spend cap, default 3).

Each iteration is appended to outputs/recursion-log.md.

Usage:
    python stretch_recursion.py [--max 3]    # real run (costs API money)
"""

import argparse
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "Basecamp-Exercises" / ".env")

HERE = Path(__file__).resolve().parent
CONTEXT_FILES = [
    "synthetic-data/rfp-acme-corp.md",
    "outputs/BTS-Synthetic_Proposal_Acme_Corp.md",
    "outputs/coordinator-transcript.txt",
]
LOG_PATH = "outputs/recursion-log.md"
FIRST_QUESTION = "What's the riskiest assumption in this proposal?"

RULES = """\
This is a REFLECTION task. Do NOT produce a docx or any other file, and do NOT run the \
full fan-out: delegate ONLY to the specialists directly relevant to the question. Keep it \
short (a few paragraphs).

End your reply with exactly ONE final line, either:
NEXT QUESTION: <the next riskiest open assumption, phrased as a question>
or, when the remaining risk is acceptable or nothing material is left to investigate:
STOP: <one-sentence reason>
"""

DECISION = re.compile(r"^[\s*_]*(NEXT QUESTION|STOP)[\s*_]*:[\s*_]*(.*?)[\s*_]*$", re.IGNORECASE)


def parse_decision(text: str) -> tuple[str, str]:
    """Last `NEXT QUESTION:` / `STOP:` line wins. Nothing found -> stop (safe default)."""
    for line in reversed(text.splitlines()):
        m = DECISION.match(line)
        if m and m.group(2):
            return ("next" if m.group(1).upper() == "NEXT QUESTION" else "stop"), m.group(2)
    return "stop", "no decision line"


def build_prompt(question: str, findings: list[tuple[str, str]], context: str) -> str:
    parts = [RULES, f"Question to investigate: {question}"]
    if findings:
        done = "\n\n".join(f"Q: {q}\nFindings:\n{r}" for q, r in findings)
        parts.append(
            "Already investigated in earlier iterations (do not repeat these):\n\n" + done
        )
    parts.append(context)
    return "\n\n".join(parts)


def run_session(client, coordinator_id: str, environment_id: str, title: str, prompt: str):
    """One new session; streams events like run_deal_desk.py. Returns (session_id, reply_text)."""
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title=title,
    )
    print(f"Session: https://platform.claude.com/sessions/{session.id}\n")
    parts: list[str] = []

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": prompt}]}],
        )
        for event in stream:
            t = event.type
            if t == "session.thread_created":
                print(f"  [thread spawned]   {event.agent_name}", flush=True)
            elif t == "agent.thread_message_received":
                print(f"  [reply ←]          {event.from_agent_name}", flush=True)
            elif t == "agent.thread_message_sent":
                print(f"  [delegate →]       {event.to_agent_name}", flush=True)
            elif t == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        parts.append(block.text)
                        print(block.text, end="", flush=True)
            elif t == "session.status_idle":
                print("\n\n[iteration finished]")
                break
    return session.id, "\n".join(parts)  # separate agent.message events so the decision line stays on its own line


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--max", type=int, default=3, help="max iterations (spend cap)")
    args = ap.parse_args(argv)
    if args.max < 1:
        raise SystemExit("--max must be >= 1")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    blocks = []
    for rel in CONTEXT_FILES:
        path = HERE / rel
        if not path.exists():
            raise SystemExit(f"Missing context file {path}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    context = "\n\n".join(blocks)

    for name in (".coordinator_id", ".environment_id"):
        if not (HERE / name).exists():
            raise SystemExit(f"Missing {HERE / name}. Run the setup scripts first.")
    coordinator_id = (HERE / ".coordinator_id").read_text().strip()
    environment_id = (HERE / ".environment_id").read_text().strip()

    client = Anthropic()
    log = HERE / LOG_PATH
    log.parent.mkdir(exist_ok=True)
    log.write_text("# Recursion log (S10)\n")

    question = FIRST_QUESTION
    findings: list[tuple[str, str]] = []
    questions: list[str] = []
    kind, detail = "next", question

    for i in range(1, args.max + 1):
        print(f"\n=== ITERATION {i}/{args.max}: {question} ===\n")
        prompt = build_prompt(question, findings, context)
        session_id, reply = run_session(
            client, coordinator_id, environment_id, f"Deal Desk — recursion {i}", prompt
        )
        findings.append((question, reply))
        questions.append(question)
        with log.open("a") as f:
            f.write(
                f"\n## Iteration {i}: {question}\n\n{reply}\n\n"
                f"Session: https://platform.claude.com/sessions/{session_id}\n"
            )
        kind, detail = parse_decision(reply)
        if kind == "stop":
            break
        question = detail

    print("\n=== SUMMARY ===")
    for n, q in enumerate(questions, 1):
        print(f"  {n}. {q}")
    if kind == "stop":
        print(f"Stopped: STOP: {detail}")
    else:
        print(f"Stopped: iteration cap ({args.max}) hit; unexplored next question: {detail}")
    print(f"Log: {log}")


if __name__ == "__main__":
    main()
