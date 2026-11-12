# Acceptance criteria — FitFindr

This file preserves the original Unit 3 agent criteria and defines five new
acceptance criteria for the local structured-logging extension.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

The first five criteria below define the current local-logging extension. The
original Unit 3 criteria are preserved afterward as baseline history.

---

## Unit extension — local structured logging

These are the five criteria for the local-serving and persistent-logging
extension. The original agent criteria from Unit 3 remain below as historical
baseline criteria.

### 1. Five successful runs produce records with required fields

Send five successful `POST /ask` requests. Each request must append exactly
one line to `results/agent_requests.jsonl`; all five lines must parse as JSON
objects and contain `timestamp` (UTC string), `request_id` (non-empty string),
`input.query` (string), `output` (object), `duration_ms` (number >= 0),
`status_code` (200), `outcome` (`success`), and `usage` fields
`model_calls`, `prompt_tokens`, `output_tokens`, and `total_tokens` (non-negative
integers) — 5 of 5 records.

**Why this target:**
These named values let me match a record to a run and inspect its result and
measured usage. The local append operation and field construction are
deterministic, so I expect all five records to satisfy the field checks.

### 2. Each of three failure types produces an error record

A rejected query, an agent-returned error session, and an exception raised by
the agent must each append exactly one record. The rejected query must have
HTTP 400 and `outcome` `invalid_query`; the returned error session must have
HTTP 200 and `outcome` `agent_error`; the raised exception must have HTTP 500
and `outcome` `server_error`. Each record must have a non-empty
`output.error` — 3 of 3 records.

**Why this target:**
These are three distinct ways a request can fail: before the agent, within its
normal return path, or by raising. Checking each expected status, outcome, and
error field makes a missing failure record directly observable.

### 3. Records persist as separate appended lines

Starting with an empty log file, send five sequential requests with distinct
query strings. After closing and reopening `results/agent_requests.jsonl`, it
must contain exactly five lines; every line must parse as one JSON object, and
the recorded queries must match the five sent queries in the same order —
5 of 5 records.

**Why this target:**
The file is intended as a durable run history, not transient console output.
Five distinct queries make overwriting, dropped lines, and reordered records
detectable; JSONL lets each record be parsed independently.

### 4. Logs include summaries and omit full wardrobe and generated text

For five requests with known wardrobe sizes, selected listing IDs, and
distinct sentinel strings in wardrobe item data, outfit suggestions, and fit
cards, each record must contain the correct `input.wardrobe_item_count` and
`output.selected_item.id`. None of the fifteen sentinel strings may occur in
the five log lines — 5 of 5 records and 0 of 15 sentinel matches.

**Why this target:**
Later diagnosis needs the wardrobe count and selected listing ID, but not
wardrobe contents or full generated text. Checking known values and sentinel
absence makes both requirements observable.

### 5. The documented command starts the local server

From a clean checkout with the documented environment set up, run
`python serve.py`. Within 30 seconds, `GET /health` must return HTTP 200 and
the exact JSON body `{"status":"ok"}` — 1 of 1 startup checks.

**Why this target:**
Persistent logging only helps if a reader can start the system outside the
editor. The 30-second limit and exact health response make the setup and
startup check repeatable and observable.

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Four of five allows one transient failure across the two model-backed tools,
while still requiring the full search, styling, and fit-card path to complete
reliably for a query known to match the dataset.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The empty-result check and branch are deterministic local code, and this path
should stop before either model-backed tool is called, so all five tries should
produce the same early stop.

---

## 3. The selected listing reaches outfit generation unchanged

In 5 of 5 matching-query runs, `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and the `suggest_outfit` trace shows the
same listing's title, price, and platform as its input.

**Why this target:**
Choosing and forwarding a listing is deterministic session logic, not model
generation; a mismatch means the wrong item could be styled, so it is not a
case where one failure is acceptable.


---

## 4. Fit cards include the purchase details

For the same matching query run 5 times, at least 4 fit cards are 2–4
sentences and mention the selected listing's title, price, and platform exactly
once each.

**Why this target:**
The model can vary its wording or miss a detail occasionally, so 4 of 5 allows
one generation miss while still requiring the caption's key facts and length
to hold in most runs.


---

## 5. Search results respect the requested price ceiling

For `vintage graphic tee under $30`, every listing in
`session["search_results"]` costs $30 or less in 5 of 5 runs.

**Why this target:**
The price filter is deterministic local code over a fixed dataset, and returning
an over-budget listing would directly violate the user's stated constraint, so
all five runs should pass.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
