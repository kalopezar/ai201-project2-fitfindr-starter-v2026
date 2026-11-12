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

### 1. Successful runs leave complete structured records

For five successful `POST /ask` requests, each request appends exactly one
valid JSON object to `results/agent_requests.jsonl`. Every record contains a
UTC timestamp, request ID, input query, output summary, non-negative duration,
HTTP status, outcome, and per-request token/model-call usage — 5 of 5 requests.

**Why this target:**
The log is the evidence used to understand an individual run later. One
missing record or essential field leaves that run uninspectable; the local
append operation and field construction are deterministic.

### 2. Failed runs are observable

A rejected query, an agent-returned error session, and an exception raised by
the agent each append a record with a non-success outcome and a useful error
description — 3 of 3 failure types.

**Why this target:**
These are three distinct ways a request can fail: before the agent, within its
normal return path, or by raising. Testing each prevents errors from becoming
silent gaps in the JSONL file.

### 3. Records persist as separate appended lines

After five sequential requests, reopening `results/agent_requests.jsonl`
produces five independently parseable JSON lines in request order, with no
prior record overwritten — 5 of 5 records.

**Why this target:**
The file is intended as a durable run history, not transient console output.
Appending rather than replacing is the central persistence behavior, and
JSONL lets each record be parsed independently.

### 4. Logs retain useful summaries without copying private payloads

For five requests containing distinct sentinel values in wardrobe item data
and generated outfit/caption text, the corresponding log records include the
wardrobe item count and selected-listing summary but contain none of those
sentinel values — 5 of 5 records.

**Why this target:**
Later diagnosis needs to know the query and which listing was selected, but
wardrobe details and full generated text are unnecessary to that diagnosis.
Keeping the log to summaries reduces sensitive and bulky data retained on
disk.

### 5. The documented local server remains runnable

From a clean checkout with the documented environment set up, running
`python serve.py` allows `GET /health` to return HTTP 200 with
`{"status":"ok"}` — 1 of 1 startup check.

**Why this target:**
Persistent logging only helps if a reader can run the system outside the
editor. The documented command and health endpoint provide a direct,
observable check that setup and startup work together.

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
