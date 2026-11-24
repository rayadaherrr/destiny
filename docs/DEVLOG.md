# Destiny – Development log

What we ran, what went wrong, how we found the cause, what we changed, and how we checked the fix.
Method every time: **run/test → see something wrong → find the cause → change the code or the instruction → test again.**

> Note: Git was set up on 29 October 2026. Work before that date is summarised below from our notes; from 29 October every change is also in the Git history (commit ids given).

---

## Before Git (21–27 October 2026)

- **data/cities.json**: 6 cities (Porto, Valencia, Seville, Barcelona, Madrid, Rome) with night price, food/day, activities/day, travel from Lisbon, tags, climate per season, high/low months.
- **schemas.py**: City, Travel, Climate, Seasons, TripRequest, TripEstimate. All TripRequest fields required but nullable (`X | None`). This fixed Gemini skipping fields.
- **pricing.py**: season ×1.3 / 1.0 / 0.8, booking ×0.8 (60+ days) to ×1.6 (last week), stay shared between people, return travel, 5 nights when no dates.
- **Decision (21 Oct)**: the night price is for the whole place and is divided by the number of people.
- **Test (21 Oct)**: same-month trips: 28–31 Oct stayed in 2026, 10 Oct moved to 2027.
- **Found (23 Oct)**: the proposal's example (3 people, 10–15 June, €500) gives no city under €500 (Porto €563). Porto in May ≈ €491, November ≈ €443.
- **26 Oct**: rebuilt the environment with `uv sync`. `page_icon=":robot_face:"` errored on Windows → changed to an emoji.
- **27 Oct**: `extraction.py` created (instruction + `extract_request` moved out of `try_request.py`). All 5 test messages still correct. `pages/1_Trip_results.py` path fixed with `Path(__file__)`.

---

## 29 October 2026

### Step 1 – Two copies of the project
- **Saw:** the folder had no `data/` or `pages/`, although both had been built on 26–27 Oct.
- **How found:** listed the outer folder too and compared. The outer one had everything; the `.py` files were identical.
- **Cause:** an old duplicate copy of the project sat inside the real one.
- **Change:** work only in the outer folder; inner one renamed `OLD_duplicate_do_not_use`; `apprsample.py` renamed `app_template.py`.

### Step 2 – "paris" gave "No cities found"
- **Ran:** `uv run streamlit run app.py`, typed "paris".
- **Saw:** "No cities found from that starting point yet."
- **How found:** that message only appears when every `estimate_cost` returns None, which happens when `city.travel_from.get(request.origin)` is None.
- **Cause:** Gemini put Paris in `origin`. TripRequest had no other place for a city.
- **Change (extraction.py):** rule "Only set origin when the user says where they start from… A city named on its own… is where they want to go… keep origin = 'lisbon'."
- **Retest:** "paris" → 6 cards ✅; "Rome in May" ✅; "From Porto, somewhere warm" → no cities (correct, no Porto data) ✅. Porto card checked by hand: 68 + 560 + 175 + 75 = €878 ✅

### Step 3 – Typos in city names
- **Change (extraction.py):** rule to correct misspelled cities + list of known city ids.
- **Retest:** "prais" → 6 cards ✅; "cheaper than barcleona" → Barcelona ✅

### Step 4 – The "I understood" line hid information
- **Saw:** "From Porto, somewhere warm" showed only "1 people · no dates". Porto and warm were missing.
- **Cause:** `show_request` only showed dates, budget, interests and cheaper_than.
- **Change (app.py):** "person"/"people", plus origin, max hours and weather in the line.
- **Retest:** "1 person · from Porto · no dates · max 3 h away · warm weather" ✅

### Step 5 – The app kept showing old behaviour
- **Saw:** terminal said the server started at 12:53 on port 8503, but the edits were made at ~13:20.
- **Cause:** an older copy of the app was still running the old code.
- **Change:** stop with Ctrl + C and start again. Rule: restart after every code change.

### Step 6 – The correction in the editable boxes was not saved
- **Ran:** changed People 3 → 2, clicked "Update results".
- **Saw:** card still said 3 people, Stay €243 (expected €364).
- **How found:** a temporary `st.caption(f"DEBUG saved people: ...")` line, then read app.py lines 118–137.
- **Cause:** the save line was indented inside an `if` block, after `return`, so it never ran. Python gives no error for that.
- **Change:** moved the line out of the `if`; removed a duplicate `show_results`; removed the DEBUG line.
- **Retest:** 2 people, Stay €364, total €685 ✅

### Step 7 – Chat history had no defined shape
- **Cause:** history items were plain dicts; a typo in a key would only fail at run time.
- **Change:** `class Turn(BaseModel)` in schemas.py; app.py uses `turn.message` / `turn.request`.
- **Note:** old history in the browser caused `AttributeError: 'dict' object has no attribute 'message'`. Fixed by refreshing / Clear conversation.

### Step 8 – Writing the tests showed a missing field
- **Saw:** for "prais" the right answer is origin lisbon *and* destination paris, but there was nowhere to put Paris.
- **Change:** `destination` field in TripRequest; extraction rule; shown in the "I understood" line; `destination=None` added in `pages/1_Trip_results.py` (otherwise ValidationError).

### Step 9 – First eval run
- **Ran:** `uv run python eval_extraction.py` on `data/examples.jsonl` (15 tests, 40 fields).
- **Result:** 14/15 messages, 38/40 fields. Passed typos, "from lisboa", words not in the descriptions ("pubs and parties" → nightlife), date rules.
- **Failed:** "this summer" → Gemini invented 1 June – 31 August (would price a 91-night trip).
- **Cause:** the instruction told Gemini to fill a field whenever the user mentions it, and TripRequest only has exact dates.

### Step 10 – Git started
- **Ran:** `git init`, `.gitignore` checked (`.env`, `.venv/`, `__pycache__/` not staged).
- **Commit:** `4bfb11e` "Destiny: current state (chat, editable boxes, pricing, eval)".

### Step 11 – Fixing the date rule, and an unstable test
- **Saw with `git diff`:** an extra `)` left from pasting.
- **Change (extraction.py):** date rules in order, ending with "For vague timing like 'this summer'… leave both dates null."
- **Eval run 2:** "this summer" ✅, but "28 to 31 October" now failed (got 2026, expected 2027). It passed in run 1, so the test was unstable.
- **Commit:** `919548d`.

### Step 12 – A prompt sentence didn't work → rule moved into code
- **Ran:** eval 3 more times. The 28–31 October test failed every time.
- **Tried (prompt):** "Decide the year by the start date…" → still failed.
- **Change (code):** `fix_year()` moves the trip one year forward while the start date is before today. Week 5: *"A sentence in the prompt changes the odds. Code changes the outcome."*
- **Commit:** `ca93c93`.
- **Later:** `fix_year` moved into `tools.py` so it applies on every path (also when the agent calls `find_trips`). Eval: **15/15 messages, 40/40 fields**.

### Step 13 – One-day trips cost €0 for food and activities
- **Saw:** test "One day trip on 10 October" → 0 nights → stay, food and activities all €0.
- **Change (pricing.py):** `days = max(nights, 1)` for food and activities; stay still uses nights.
- **Error while changing:** `NameError: name 'total_eur' is not defined`. The pasted block had dropped the `total_eur = ...` line. Found from the traceback; line added back.
- **Commit:** `28e0bd3`.

---

## 31 October 2026

### Step 14 – tools.py ready for the agent
- **Change:** `TOOLS`, `ASK_FIRST`, `DECLARATIONS` and `run_tool()` (Week 5 shape) with `find_trips`.
- **Ran:** `uv run python try_tools.py`: by hand and through `run_tool` → same cities (Porto €563 … Rome €963); unknown tool → "There is no tool called book_flight…"; missing field → "Invalid origin: Field required. Fix it and call again." All as expected.
- **Commit:** `984f424`, pushed to GitHub.

---

## 24 November 2026

### Step 15 – Any city in the list as the starting point (branch `any-city`)
- **Why:** the teacher said that having Lisbon as the only starting point is weak.
- **Cause in the code:** each city stores only its route from Lisbon (`travel_from: {"lisbon": ...}`), used in `schemas.py`, `pricing.py`, `tools.py` and `views/trip_finder.py` (the map). Any other origin gives "No cities found".
- **Plan:** store each city's `lat`/`lon`, remove `travel_from`, calculate travel between any two cities in a new `travel.py` (distance → mode, hours, cost), then add more cities.
- **Baseline before any-city (24 Nov 2026, gemini-flash-lite-latest):** 15/15 messages, 40/40 fields (`uv run python eval_extraction.py`).
- **Agreed with Shaahir (24 Nov):** coordinates go into `cities.json`; `geo.py` stays for now because the map uses it; delete it later once the map reads `lat`/`lon` from `cities.json`.
- **Changes:**
  - `schemas.py`: City gets `lat` and `lon` (floats, with descriptions; west of Greenwich is negative); `travel_from` kept for now (the map still uses it)
- **Retest:** *(fill in as we go)*
