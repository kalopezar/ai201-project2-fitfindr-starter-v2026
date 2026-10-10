"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import MCPError, call_tool
from generate import ModelUnavailable
from tools import suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    next_step = "parse"
    active_tool = "query parsing"
    count = 0

    try:
        while next_step != "done":
            count += 1
            trace.check_iterations(count)

            if next_step == "parse":
                active_tool = "query parsing"
                session["parsed"] = parse_query(query)
                trace.step("parse_query", inputs=query, returned=session["parsed"])
                next_step = "search"

            elif next_step == "search":
                active_tool = "search_listings (via MCP)"
                parsed = session["parsed"]
                session["search_results"] = call_tool("search_listings", parsed)
                if not session["search_results"]:
                    session["error"] = _no_results_message(parsed)
                    trace.step(
                        active_tool,
                        inputs=parsed,
                        returned=session["search_results"],
                        note="branch: empty; stopping before suggest_outfit",
                    )
                    next_step = "done"
                else:
                    trace.step(
                        active_tool,
                        inputs=parsed,
                        returned=session["search_results"],
                    )
                    session["selected_item"] = session["search_results"][0]
                    next_step = "suggest"

            elif next_step == "suggest":
                active_tool = "suggest_outfit"
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
                trace.step(
                    active_tool,
                    inputs=session["selected_item"],
                    returned=session["outfit_suggestion"],
                )
                next_step = "fit_card"

            elif next_step == "fit_card":
                active_tool = "create_fit_card"
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
                trace.step(
                    active_tool,
                    inputs={"outfit": session["outfit_suggestion"],
                            "new_item": session["selected_item"]},
                    returned=session["fit_card"],
                )
                next_step = "done"
    except (MCPError, ModelUnavailable) as exc:
        if isinstance(exc, MCPError):
            session["error"] = (
                "search_listings (via MCP) failed: listing search could not reach "
                "the MCP server. Retry the search; if it keeps failing, check "
                "the MCP server connection."
            )
        elif active_tool == "suggest_outfit":
            session["error"] = (
                "suggest_outfit failed: outfit suggestions could not be generated "
                "because the model is unavailable. Check the model API key or "
                "connection, then retry."
            )
        else:
            session["error"] = (
                "create_fit_card failed: fit-card generation could not be "
                "completed because the model is unavailable. Check the model "
                "API key or connection, then retry."
            )
        trace.step(active_tool, note=f"failed ({type(exc).__name__}); see session error")

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|max|up to)\s*\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE_RE = re.compile(r"\bsize\s+([a-z0-9./]+)", re.IGNORECASE)
_FILLER_RE = re.compile(r"\b(?:i'?m\s+)?(?:looking for|i want|find me|show me)\b", re.IGNORECASE)


def parse_query(query: str) -> dict:
    """
    Pull a description, size, and max_price out of a plain-language query,
    using regex. Anything not recognised as a price or size stays in the
    description.

        "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    text = query

    max_price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[:price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[:size_match.start()] + " " + text[size_match.end():]

    text = _FILLER_RE.sub(" ", text)
    description = " ".join(re.sub(r"[,;]", " ", text).split())

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Tell the user what they could change, based on which filters were on."""
    suggestions = []
    if parsed["max_price"] is not None:
        suggestions.append(f"raise the price limit above ${parsed['max_price']:g}")
    if parsed["size"]:
        suggestions.append(f"drop the size filter ({parsed['size']})")
    suggestions.append("use fewer or more general keywords")
    return (
        f"Nothing matched \"{parsed['description']}\". "
        f"Try to {', or '.join(suggestions)}."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
