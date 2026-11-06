"""
Deck-only run: the coordinator builds a 5-slide HTML pitch deck from the
previous run's outputs, and every `write` tool call for outline.json /
slide-N.html is mirrored to outputs/deck/ LIVE so deck_viewer.html (served on
http://localhost:8765/) can animate the slides in.

Usage:
    python run_deck_live.py                             # real run (costs API money)
    python run_deck_live.py --agents-url URL            # open split view (agents | deck)
    python run_deck_live.py --selftest                  # offline check of the mirror logic

Reusable from another runner:
    state = setup(); start_viewer(agents_url=...)
    for event in stream: on_event(event, state)
    fetch_missing(client, session_id, state)
"""

import functools
import http.server
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
import threading
import types
import webbrowser
from pathlib import Path
from urllib.parse import quote

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "Basecamp-Exercises" / ".env")

HERE = Path(__file__).resolve().parent
DECK_DIR = HERE / "outputs" / "deck"
PORT = 8765
ALLOWED = re.compile(r"outline\.json|slide-\d+\.html")
CONTEXT_FILES = [
    "synthetic-data/rfp-acme-corp.md",
    "outputs/coordinator-transcript.txt",
    "outputs/acme-corp-commercial-recommendation.md",
    "deck_style.md",
]

DECK_ONLY = """\
This is a DECK-ONLY task. Do NOT delegate to specialists and do NOT produce a docx. \
The specialists' work is already in the attached documents.
"""

TASK = """\
Build a 5-slide executive pitch deck for the Acme Corp proposal. Suggested arc: \
title/exec summary, customer need, why us, commercial proposal, contract approach & \
risks / next step (you may adjust).

Step 1: use the `write` tool to write /mnt/session/outputs/deck/outline.json containing \
{"title": "...", "slides": [{"title": "..."}, ...5 entries]}.

Step 2: write the slides one at a time, in order, to /mnt/session/outputs/deck/slide-1.html \
... slide-5.html. Use exactly ONE `write` tool call per slide. Never use bash, heredocs, \
python or edit for these files: the live viewer only sees `write` calls. Before each slide, \
send one short sentence of narration (it is shown live in the viewer).

Each slide file is an HTML FRAGMENT: no <html>/<head>/<body>, no <script>. The root element \
is `<section class="slide">`. Use ONLY the classes documented in deck_style.md below; a small \
inline <style> scoped under `.slide` is allowed but discouraged. Keep content tight: max ~40 \
words of body text per slide, numbers taken from the documents, no invented facts.

Finish with a one-line summary.
"""


# ---------- mirror / state logic (pure, testable) ----------

def new_state() -> dict:
    return {"title": "", "total": 5, "slides": [], "log": "", "phase": "starting"}


def save_state(state: dict, deck_dir: Path) -> None:
    atomic_write(deck_dir / "state.json", json.dumps(state, indent=2))


def atomic_write(dest: Path, text: str) -> None:
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, dest)


def advance_drafting(state: dict) -> None:
    """Mark the first not-done slide as drafting; the rest stay pending."""
    found = False
    for s in state["slides"]:
        if s["status"] == "done":
            continue
        s["status"] = "pending" if found else "drafting"
        found = True


def handle_write(file_path: str, content: str, state: dict, deck_dir: Path) -> bool:
    """Mirror one agent `write` call. Returns True if it was accepted."""
    parts = file_path.split("/")
    name = posixpath.basename(file_path)
    if ".." in parts or len(parts) < 2 or parts[-2] != "deck" or not ALLOWED.fullmatch(name):
        return False
    deck_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(deck_dir / name, content)

    if name == "outline.json":
        try:
            outline = json.loads(content)
            titles = [str(s.get("title", "")) for s in outline["slides"]]
        except (ValueError, KeyError, TypeError, AttributeError):
            return True  # file mirrored, but unusable for state
        state["title"] = str(outline.get("title", ""))
        state["total"] = len(titles) or state["total"]
        old = {s["n"]: s for s in state["slides"]}
        state["slides"] = [
            {"n": i, "title": t, "status": old.get(i, {}).get("status", "pending"),
             "rev": old.get(i, {}).get("rev", 0)}
            for i, t in enumerate(titles, 1)
        ]
        state["phase"] = "building"
    else:
        n = int(name[len("slide-"):-len(".html")])
        while len(state["slides"]) < n:  # slide arrived before/without an outline
            state["slides"].append({"n": len(state["slides"]) + 1, "title": "", "status": "pending", "rev": 0})
        state["slides"][n - 1]["status"] = "done"
        state["slides"][n - 1]["rev"] += 1
        state["phase"] = "building"
    advance_drafting(state)
    save_state(state, deck_dir)
    return True


def handle_message(blocks, state: dict, deck_dir: Path) -> None:
    texts = [b.text.strip() for b in blocks if getattr(b, "type", None) == "text" and b.text.strip()]
    if state["phase"] == "starting":
        state["phase"] = "outlining"
    if texts:
        state["log"] = " ".join(texts[-1].split())[:140]
    save_state(state, deck_dir)


def handle_idle(state: dict, deck_dir: Path) -> None:
    state["phase"] = "done"
    save_state(state, deck_dir)


# ---------- live run ----------

def setup(deck_dir: Path = DECK_DIR) -> dict:
    """Clear the deck dir, copy the viewer pages in, write the initial state.json."""
    deck_dir.mkdir(parents=True, exist_ok=True)
    for old in [*deck_dir.glob("slide-*.html"), deck_dir / "outline.json", deck_dir / "state.json"]:
        old.unlink(missing_ok=True)
    for src, dest in [("deck_viewer.html", "index.html"), ("split.html", "split.html")]:
        if not (HERE / src).exists():
            raise SystemExit(f"Missing {HERE / src}")
        shutil.copy(HERE / src, deck_dir / dest)
    state = new_state()
    save_state(state, deck_dir)
    return state


def context() -> str:
    """The inlined documents (incl. deck_style.md) the coordinator needs."""
    blocks = []
    for rel in CONTEXT_FILES:
        path = HERE / rel
        if not path.exists():
            raise SystemExit(f"Missing context file {path}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def start_viewer(agents_url: str | None = None) -> None:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = functools.partial(Handler, directory=str(DECK_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    page = f"split.html?agents={quote(agents_url, safe='')}" if agents_url else ""
    url = f"http://localhost:{PORT}/{page}"
    webbrowser.open(url)
    print(f"Viewer: {url}")


def on_event(event, state: dict, deck_dir: Path = DECK_DIR) -> None:
    """Mirror one session event into deck_dir and state.json; unknown types are ignored."""
    t = getattr(event, "type", None)
    if t == "agent.message":
        if getattr(event, "session_thread_id", None) is not None:
            return  # sub-agent thread: not the coordinator's deck narration
        for b in event.content:
            if getattr(b, "type", None) == "text":
                print(b.text, end="", flush=True)
        handle_message(event.content, state, deck_dir)
    elif t == "agent.tool_use":
        inp = getattr(event, "input", None) or {}
        ok = False
        if event.name == "write":
            ok = handle_write(str(inp.get("file_path", "")), str(inp.get("content", "")), state, deck_dir)
        print(f"\n  [tool: {event.name}{' -> mirrored ' + posixpath.basename(inp['file_path']) if ok else ''}]", flush=True)
    elif t == "session.status_idle":
        print("\n\n[agent finished]")
        handle_idle(state, deck_dir)


def fetch_missing(client, session_id: str, state: dict, deck_dir: Path = DECK_DIR) -> None:
    """Fallback: fetch anything the live mirror missed."""
    files = client.beta.files.list(scope_id=session_id, betas=["managed-agents-2026-04-01"])
    for f in files.data:
        name = posixpath.basename(f.filename)
        if not ALLOWED.fullmatch(name) or (deck_dir / name).exists():
            continue
        print(f"  fallback download: {name}")
        with tempfile.TemporaryDirectory() as tmp:
            client.beta.files.download(f.id).write_to_file(str(Path(tmp) / name))
            handle_write(f"/mnt/session/outputs/deck/{name}", (Path(tmp) / name).read_text(), state, deck_dir)
    handle_idle(state, deck_dir)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")
    agents_url = sys.argv[sys.argv.index("--agents-url") + 1] if "--agents-url" in sys.argv else None
    coordinator_id = (HERE / ".coordinator_id").read_text().strip()
    environment_id = (HERE / ".environment_id").read_text().strip()

    state = setup()
    start_viewer(agents_url)
    user_message = DECK_ONLY + "\n" + TASK + "\n\n" + context()

    client = Anthropic()
    session = client.beta.sessions.create(
        agent=coordinator_id,
        environment_id=environment_id,
        title="Deal Desk — Acme Corp deck (live)",
    )
    print(f"Session: https://platform.claude.com/sessions/{session.id}\n")

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": user_message}]}],
        )
        for event in stream:
            on_event(event, state)
            if event.type == "session.status_idle":
                break

    fetch_missing(client, session.id, state)

    print(f"\nSession: https://platform.claude.com/sessions/{session.id}")
    input("Press Enter to stop the viewer server...")


# ---------- offline self-check ----------

def selftest() -> None:
    class B:  # fake text block
        type = "text"
        def __init__(self, text): self.text = text

    with tempfile.TemporaryDirectory() as tmp:
        d, state = Path(tmp), new_state()
        status = lambda: [s["status"] for s in state["slides"]]
        saved = lambda: json.loads((d / "state.json").read_text())

        handle_message([B("  "), B("Outlining now.\n  Really.")], state, d)
        assert state["phase"] == "outlining" and state["log"] == "Outlining now. Really."

        outline = json.dumps({"title": "Acme", "slides": [{"title": f"S{i}"} for i in range(1, 6)]})
        P = "/mnt/session/outputs/deck/"
        assert handle_write(P + "outline.json", outline, state, d)
        assert state["phase"] == "building" and status() == ["drafting"] + ["pending"] * 4

        assert handle_write(P + "slide-1.html", "<section class='slide'>1</section>", state, d)
        assert status() == ["done", "drafting", "pending", "pending", "pending"]
        assert (d / "slide-1.html").read_text() == "<section class='slide'>1</section>"

        # out-of-order slide + rewrite bumps rev
        assert handle_write(P + "slide-3.html", "x", state, d)
        assert status() == ["done", "drafting", "done", "pending", "pending"]
        assert handle_write(P + "slide-1.html", "y", state, d) and state["slides"][0]["rev"] == 2

        # rejected paths: traversal, wrong dir, wrong name
        for bad in ["/mnt/session/outputs/deck/../../etc/slide-9.html", "/mnt/session/outputs/slide-2.html",
                    P + "evil.html", P + "slide-2.html.sh", "slide-2.html", P + "sub/../x/slide-2.html"]:
            assert not handle_write(bad, "nope", state, d), bad
        assert status() == ["done", "drafting", "done", "pending", "pending"]
        assert not (d / "evil.html").exists() and not (d / "slide-9.html").exists()

        for n in (2, 4, 5):
            handle_write(P + f"slide-{n}.html", "z", state, d)
        assert status() == ["done"] * 5

        handle_idle(state, d)
        s = saved()
        assert s["phase"] == "done" and s == state and s["title"] == "Acme" and s["total"] == 5

    # on_event with fake event objects
    ns = types.SimpleNamespace
    with tempfile.TemporaryDirectory() as tmp:
        d, state = Path(tmp), new_state()
        write = lambda path, content: ns(type="agent.tool_use", name="write", input={"file_path": path, "content": content})
        msg = lambda text, thread=None: ns(type="agent.message", content=[B(text)], session_thread_id=thread)

        on_event(ns(type="span.something_new"), state, d)  # unknown type: ignored
        on_event(msg("Outlining."), state, d)
        assert state["log"] == "Outlining." and state["phase"] == "outlining"
        on_event(write(P + "outline.json", outline), state, d)
        on_event(write(P + "slide-1.html", "<section class='slide'>1</section>"), state, d)
        on_event(ns(type="agent.tool_use", name="bash", input={"command": "ls"}), state, d)
        on_event(msg("Researching pricing.", "thread_abc"), state, d)  # sub-agent: must not touch log
        assert state["log"] == "Outlining."
        on_event(msg("Slide two.", None), state, d)
        assert state["log"] == "Slide two."
        assert [s["status"] for s in state["slides"]] == ["done", "drafting", "pending", "pending", "pending"]
        assert json.loads((d / "state.json").read_text())["slides"][0]["rev"] == 1
        on_event(ns(type="session.status_idle"), state, d)
        assert state["phase"] == "done" and json.loads((d / "state.json").read_text()) == state
    print("selftest OK")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
