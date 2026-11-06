# Handoff: live agent view + live deck, side by side

For the agent implementing the **live sub-agent view**. The deck side and the split page are done.
Your job: build the agent view on your own backend, run the full swarm session, and drive our deck
mirror from your event loop with three function calls.

## What already exists (don't rebuild)

| File | What it is |
|---|---|
| `run_deck_live.py` | Copies the coordinator's slide `write` calls from the session event stream into `outputs/deck/`, keeps `outputs/deck/state.json` current, serves `outputs/deck/` on **http://localhost:8765**. It's importable; standalone it runs a deck-only session. |
| `deck_viewer.html` | Live deck page (served as `index.html`). Polls `state.json` once a second and animates slides in. |
| `split.html` | Side-by-side shell (served as `split.html`). **Left:** iframe of `?agents=<url>` (default `http://localhost:8766/`). **Right:** our `index.html`. Draggable divider. Shows "Waiting for agent view…" and re-checks every 2s until your URL answers. |
| `deck_style.md` | Slide CSS class reference. It must be in the coordinator's prompt. |

Open: `http://localhost:8765/split.html?agents=<your url, URL-encoded>`. `deck.start_viewer(agents_url=...)` opens it for you.

## Your contract (what the left pane needs from you)

1. **Serve your view over HTTP** at a URL of your choice (suggested: `http://localhost:8766/`). Its root must answer a plain GET, because the split page checks it with `fetch(url, {mode: "no-cors"})`.
2. **Allow it to be framed:** no `X-Frame-Options: DENY/SAMEORIGIN`, and no CSP `frame-ancestors` that excludes `http://localhost:8765`. A cross-origin iframe is fine, and no CORS is needed.
3. **Lay it out for about half the screen:** about 780×850px on a 1600px screen. The divider can be dragged anywhere from 20% to 80% of the width.
4. **Match the look (optional):** Anthropic palette with an XP-window homage. CSS vars: `--ivory:#F0EEE6 --cream:#FAF9F5 --ink:#141413 --clay:#D97757 --slate:#5E5D59 --border:#E8E6DC`. Serif headings ("Source Serif 4"), sans body ("Inter"), mono labels ("JetBrains Mono"). `split.html` already draws an "Agents" window title bar above your iframe, so leave the outer chrome to us.

## Wiring the deck into your runner

You own the session (the full swarm: specialists, synthesis, deck). Consume the **same** event stream for both views:

```python
import run_deck_live as deck   # sits next to your runner in specialist-swarm/

state = deck.setup()                                   # clears outputs/deck, copies index.html + split.html, writes state.json
deck.start_viewer(agents_url="http://localhost:8766/") # serves :8765, opens split.html?agents=...

style = (deck.HERE / "deck_style.md").read_text()
user_message = (
    YOUR_SWARM_INSTRUCTIONS                            # delegate to specialists, synthesise, ...
    + "\n\nFinally, build the slide deck:\n" + deck.TASK
    + "\n\n=====  DOCUMENT: deck_style.md  =====\n" + style
    + "\n\n" + YOUR_RFP_CONTEXT
)

with client.beta.sessions.events.stream(session.id) as stream:
    client.beta.sessions.events.send(session.id, events=[{"type": "user.message",
        "content": [{"type": "text", "text": user_message}]}])
    for event in stream:
        your_agent_view.push(event)                    # your side
        deck.on_event(event, state)                    # our side: mirrors outline.json / slide-N.html, updates state.json
        if event.type == "session.status_idle" and YOUR_RUN_IS_REALLY_DONE:
            break

deck.fetch_missing(client, session.id, state)          # fallback download of any slide the live mirror missed
```

Don't use `deck.context()` in a full-swarm run. It inlines the *previous* run's outputs, which is meant for deck-only mode.

### Public API of `run_deck_live.py`

```python
setup(deck_dir=DECK_DIR) -> dict                       # returns the state dict you pass around
start_viewer(agents_url: str | None = None) -> None    # None opens the deck alone (index.html)
on_event(event, state, deck_dir=DECK_DIR) -> None      # safe to call with every event; ignores unknown types
fetch_missing(client, session_id, state, deck_dir=DECK_DIR) -> None
TASK: str                                              # deck-building instructions for the coordinator
HERE: Path                                             # specialist-swarm/
```

## Gotchas

- **Only `write` tool calls are mirrored**, for `.../deck/outline.json` and `.../deck/slide-<n>.html` (the parent folder must be named `deck`). `TASK` already tells the coordinator this. If your swarm prompt tells it to use bash or python for files, it can override that, and slides will then only appear at the end via `fetch_missing`.
- **Idle mid-run:** `on_event` marks the deck "done" on *every* `session.status_idle`. In a multi-agent session the coordinator can go idle while it waits for specialists. If that happens before the deck is built, the deck shows "complete" too early. Fix: call `on_event` only for non-idle events and call `deck.handle_idle(state, deck.DECK_DIR)` yourself when the run is really over.
- **Sub-agent messages:** `agent.message` events with a non-`None` `session_thread_id` (sub-agent threads) don't change the deck's narration line. That's the data your view wants, and the deck deliberately ignores it.
- **Ports:** 8765 is ours. Pick anything else for yours. If you don't use 8766, pass your URL via `agents_url`.
- **Keep the process alive** after the loop (e.g. `input()`), or both servers die with it.

## Checking your side without the API

```bash
python run_deck_live.py --selftest        # our mirror logic, offline
# Fake a deck: copy deck_viewer.html -> some_dir/index.html and split.html -> some_dir/, add a state.json
# (schema: see new_state() / handle_write in run_deck_live.py), then
cd some_dir && python3 -m http.server 8765
# start your view on 8766, open http://localhost:8765/split.html?agents=http%3A%2F%2Flocalhost%3A8766%2F
```

Run Python with `/Users/max/00_code/anthropic_basecamp_sovai_key/.venv/bin/python`. The API key loads from `Basecamp-Exercises/.env` (see the repo's `CLAUDE.md`).
