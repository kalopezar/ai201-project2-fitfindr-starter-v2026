# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

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
