# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps someone search thrift listings with a plain-language request, including optional size and price limits. It returns matching items ranked by keyword match. It can suggest outfits using pieces in the user's wardrobe, or general styling ideas when the wardrobe is empty. It also creates a short social caption for the outfit, while an empty search returns suggestions for broadening the query.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches thrift listings for description keywords, with optional size and inclusive maximum-price filters, then ranks matches by keyword overlap. Matching lowercases and splits on non-alphanumeric characters, ignores one-character tokens and `a`, `an`, `and`, `are`, `as`, `at`, `be`, `by`, `for`, and `from`, then scores each distinct query token as 2 for a title/category/style-tag hit or otherwise 1 for a description/color/brand hit; zero-score listings are dropped, results sort by score descending, and dataset order breaks ties.
- **Inputs:** `description` (`str`); `size` (`str | None`); `max_price` (`float | None`). A requested size matches a complete size token (so `M` matches `S/M`); `One Size` listings match any requested size.
- **Returns:** A `list[dict]` of matching listing records, ranked best first and limited to `config.SEARCH_RESULT_LIMIT`. Each record has `id`, `title`, `description`, `category`, `style_tags` (`list[str]`), `size`, `condition`, `price` (`float`), `colors` (`list[str]`), `brand` (`str | None`), and `platform`.
- **When it has nothing:** Returns `[]` when no useful description keywords are provided or no listing matches all supplied filters and at least one keyword.

### `suggest_outfit`

- **What it does:** Uses the language model to suggest one or two outfits built around a thrift listing, using owned wardrobe pieces when available.
- **Inputs:** `new_item` (`dict`, one listing record with the fields described above); `wardrobe` (`dict` with an `items` key containing `list[dict]` wardrobe pieces, each with `id`, `name`, `category`, `colors`, `style_tags`, and optional `notes`).
- **Returns:** A non-empty `str` containing outfit suggestions. With wardrobe items, suggestions name and use only listed pieces; with no items, the string gives general styling ideas.
- **When it has nothing:** An empty wardrobe is not a no-result: it gets general styling advice. If the model returns an empty response, the tool returns a non-empty retry message instead of `""`.

### `create_fit_card`

- **What it does:** Uses the language model to write a casual social caption for an outfit featuring a thrifted listing.
- **Inputs:** `outfit` (`str`, an outfit suggestion); `new_item` (`dict`, one listing record with the fields described above).
- **Returns:** A `str` caption of two to four sentences, mentioning the item, price, and platform once each and describing the look's vibe.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a descriptive message asking for an outfit suggestion first. If the model returns an empty response for a non-empty outfit, returns a short fallback caption.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a no-results message in the session and stop. Otherwise, take the first result and go to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract an optional price ceiling and `size ...` filter; another regex removes common request lead-ins, and the remaining words become the search description.

**What moves through the session:** `query` is parsed into `parsed`; `search_results` stores the tool results; the first result is copied to `selected_item` and passed with `wardrobe` to `suggest_outfit`; its string goes to `outfit_suggestion` and, with `selected_item`, to `create_fit_card`, whose result is stored in `fit_card`. If search is empty, `error` is set and the later fields remain unset.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

     Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

     Outfit:   Grab it! That butterfly tee is a total win.

Outfit one: Pair the Y2K Baby Tee — Butterfly Print with your Baggy straight-leg jeans, dark wash and Chunky white sneakers. Throw on the Vintage black denim jacket over top for that effortless early-2000s model-off-duty vibe.

Outfit two: Tuck the tee into your Wide-leg khaki trousers, cinch it with the Brown leather belt, and wear your Black combat boots. Toss the Black cropped zip hoodie over your shoulders or wear it unzipped to finish the look.

     Fit card: Found the ultimate early 2000s model-off-duty fit by styling this little butterfly baby tee with my favorite baggy dark-wash jeans and a vintage denim jacket. Snagged the top for just $18 over on depop and it’s honestly in the best condition. Such an easy throw-on-and-go look. #y2kstyle #thrifted

0 model calls this session, 2 served from cache

```

**Empty-search branch**

```
$ python app.py ask 'designer ballgown size XXS under $5'

     Nothing matched "designer ballgown". Try to raise the price limit above $5, or drop the size filter (XXS), or use fewer or more general keywords.

0 model calls this session

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; matches = search_listings('graphic tee', max_price=30); empty = search_listings('zzzzqxv'); assert matches and all(item['price'] <= 30 for item in matches); assert empty == []; print(([(item['title'], item['price'], item['size'], item['platform']) for item in matches], empty))"
([('Y2K Baby Tee — Butterfly Print', 18.0, 'S/M', 'depop'), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0, 'L', 'depop'), ('Vintage Band Tee — Faded Grey', 19.0, 'L', 'depop'), ('Vintage Graphic Hoodie — Faded Black', 26.0, 'L', 'depop'), ('Mesh Long-Sleeve Top — Black', 15.0, 'S/M', 'depop'), ('Low-Rise Cargo Pants — Khaki', 27.0, 'W29', 'poshmark')], [])
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; answer = suggest_outfit(load_listings()[0], get_empty_wardrobe()); assert isinstance(answer, str) and answer.strip(); print(answer.replace('\n', ' '))"
Grab those 501s immediately! Vintage Levi’s are the holy grail of thrift shopping. Since they have that great medium wash and broken-in knee fade, they are super versatile.   For an easy casual look, pair them with a boxy white graphic tee, some well-worn white sneakers, and a classic canvas tote bag. Throw on a simple silver chain to finish it off.   For something a bit sharper, dress them up with an oversized black blazer layered over a fitted ribbed tank top. Add some retro leather loafers and a sleek black belt to tie the whole outfit together.   You will wear these constantly!
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; item = load_listings()[0]; caption = create_fit_card('jeans and white sneakers', item); empty = create_fit_card('   ', item); assert isinstance(caption, str) and caption.strip(); assert empty.startswith('No outfit to caption yet'); print((caption.replace('\n', ' '), empty))"
("Nothing beats finding a pair of vintage Levi’s 501s that actually fit right in the waist. Snagged these for $38 on depop and honestly haven't taken them off since with my beat-up white sneakers. It's giving that effortless 90s streetwear vibe without even trying. #thriftfinds", "No outfit to caption yet for Vintage Levi's 501 Jeans — Medium Wash — get an outfit suggestion first, then make the fit card.")
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Copilot to specify each tool's inputs, return values, and empty cases before implementation.
- *What came back:* The first search description said only that results were ranked by "keyword overlap," which left the matching fields and scoring ambiguous.
- *What I changed:* I challenged whether another developer could implement that description without clarification, then added the tokenization, stopwords, field weights, zero-score rule, and tie behavior to the Tool Inventory.

**Moment 2**

- *What I asked for:* I asked Copilot to run both a matching query and an impossible query, print the session, and check whether the selected listing was the one sent to `suggest_outfit`.
- *What came back:* The matching run selected `lst_002` as the first search result and passed that same item to `suggest_outfit`; the impossible query left `fit_card` as `None` and suggested which filters or keywords to change.
- *What I changed:* I recorded the parsing and session flow plus both CLI outcomes in this README, and verified the handoff with a tool-call spy.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
