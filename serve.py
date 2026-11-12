#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

Each /ask request appends one structured JSON record to
`results/agent_requests.jsonl`. It includes the query and a summary of the
agent output, but not wardrobe contents, generated text, or credentials.
"""

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, jsonify, request

from agent import run_agent
from generate import usage_snapshot
from utils.data_loader import get_example_wardrobe

app = Flask(__name__)
LOG_PATH = config.RESULTS_DIR / "agent_requests.jsonl"
_log_lock = threading.Lock()


def _log_agent_request(
    request_id: str,
    started_at: float,
    status_code: int,
    outcome: str,
    usage_before: dict[str, int],
    usage_after: dict[str, int],
    input_summary: dict,
    output_summary: dict,
    error_type: str | None = None,
) -> None:
    usage = {
        key: usage_after[key] - usage_before[key]
        for key in usage_before
    }
    record = {
        "event": "agent_request",
        "timestamp": datetime.now(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z"),
        "request_id": request_id,
        "method": request.method,
        "path": request.path,
        "status_code": status_code,
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "outcome": outcome,
        "model_id": config.MODEL,
        "input": input_summary,
        "output": output_summary,
        "usage": usage,
    }
    if error_type is not None:
        record["error_type"] = error_type
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _log_lock:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(line)
            log_file.flush()


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← right: the DEFAULT sync worker
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make

_one_at_a_time = threading.Lock()


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON.
    """
    request_id = uuid.uuid4().hex
    started_at = time.perf_counter()
    empty_usage = usage_snapshot()
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    query = payload.get("query")
    if isinstance(query, str):
        query = query.strip()
    else:
        query = ""
    input_summary = {"query": query, "wardrobe_item_count": 0}
    if not query:
        # 400 rather than a stack trace: the caller can act on this one.
        _log_agent_request(
            request_id,
            started_at,
            400,
            "invalid_query",
            empty_usage,
            empty_usage,
            input_summary,
            {"error": "A non-empty query is required."},
        )
        return jsonify({"error": "Send JSON with a 'query' field, e.g. "
                                 '{"query": "vintage graphic tee under $30"}'}), 400

    wardrobe = payload.get("wardrobe")
    if not isinstance(wardrobe, dict):
        wardrobe = get_example_wardrobe()
    wardrobe_items = wardrobe.get("items")
    input_summary["wardrobe_item_count"] = (
        len(wardrobe_items) if isinstance(wardrobe_items, list) else 0
    )

    # A queued request should look like a queued request. Without this the
    # second caller just sits there, and "slow" and "waiting its turn" are
    # indistinguishable from the outside — which is how people conclude the
    # deployment is broken when it is behaving exactly as designed.
    #
    # This supplements the JSON completion record with an immediate note for a
    # queued caller. `locked()` can be a moment out of date, so the note is
    # occasionally missed — which costs nothing, because nothing depends on it.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    failure = None
    failure_type = None
    session = None
    with _one_at_a_time:
        usage_before = usage_snapshot()
        try:
            session = run_agent(query, wardrobe)
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            failure = f"{type(exc).__name__}: {exc}"
            failure_type = type(exc).__name__
        usage_after = usage_snapshot()

    # Outside the lock: building a response is not work the next caller should
    # be waiting on.
    if failure is not None:
        _log_agent_request(
            request_id,
            started_at,
            500,
            "server_error",
            usage_before,
            usage_after,
            input_summary,
            {"error": failure},
            failure_type,
        )
        return jsonify({"error": failure}), 500

    outcome = "agent_error" if session["error"] else "success"
    selected_item = session.get("selected_item")
    selected_summary = None
    if isinstance(selected_item, dict):
        selected_summary = {
            key: selected_item.get(key)
            for key in ("id", "title", "price", "platform")
        }
    output_summary = {
        "error": session.get("error"),
        "selected_item": selected_summary,
        "has_outfit_suggestion": bool(session.get("outfit_suggestion")),
        "has_fit_card": bool(session.get("fit_card")),
    }
    _log_agent_request(
        request_id,
        started_at,
        200,
        outcome,
        usage_before,
        usage_after,
        input_summary,
        output_summary,
    )
    return jsonify(session)


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print("Ctrl-C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
