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

- **Changes (in order):**
  1. `schemas.py`: City gets `lat` and `lon` (floats, with descriptions; west of Greenwich is negative); `travel_from` kept for now (the map still uses it).
  2. `cities.json`: added `lat`/`lon` to the 6 cities (values from Shaahir's `geo.py`).
  3. `cities.json`: added Lisbon (lat/lon; night price €150 = Inside Airbnb median for entire homes, Dec 2025; food/activities estimated) + new `docs/data_model.md` (what each field means, sources, climate rule).
     - **Bug:** Saw: `JSONDecodeError: Expecting ',' delimiter: line 104`. Cause: no comma after Rome's closing `}` when Lisbon was pasted below it. Fix: `}` → `},` on line 103. Retest: the file loads, 7 cities.
  4. `travel.py` (new): `distance_km` (haversine) + `travel_between` (< 400 km train: km/90 h, €0.12/km; otherwise flight: 0.75 + km/800 h, €50 + €0.027/km; fitted to the old Lisbon routes). Checked with `try_travel.py`: Lisbon→Porto 274 km, 3.0 h, €33 train; Madrid→Rome 1364 km, 2.5 h, €87 flight.
  5. `pricing.py`: `estimate_cost` now receives the travel (3rd input) instead of looking it up in `travel_from`.
  6. `tools.py`: `find_trips` finds the start city (clear failure if it isn't one of ours), skips it as a destination, and calculates travel with `travel_between` for every city.
     - **Bug:** Saw: `IndentationError: unindent does not match any outer indentation level (tools.py, line 88)`. Cause: the new `reference = ...` line had 9 spaces instead of 8. Fix: lined it up with `limit`. Retest: file runs.
     - **Bug:** Saw (reading the diff): the destination filter (`if args.destination and city.id != args.destination: continue`) had been deleted while replacing the loop lines, so "to Rome" would show every city. Fix: added it back as the first check in the loop.
  7. `extraction.py`: the list of known city ids for Gemini is now built from `cities.json` (`load_cities()`) instead of typed by hand, so new cities are known automatically.
  8. `cities.json`: 23 new cities (30 in total) chosen for variety: beach, nature, nightlife, cheap and expensive, warm in winter (Las Palmas), 15 countries. lat/lon accurate; night/food/activity prices are estimates (see `data_model.md`).
     - **Bug:** same missing comma as in change 3, this time after Lisbon's `}` (line 118). Pattern: every time a city is pasted after the last one, the previous `}` needs a comma.
  9. Tests updated: `try_tools.py` test 5 used "from Paris" to check a start city we don't have; Paris is now ours, so test 5 is now "from Ibiza" and test 6 checks "from Paris" works. `examples.jsonl`: new test "I want to go to Ibiza" (a city we don't have → destination ibiza, origin stays lisbon).
  10. `data_model.md`: sources per group of cities; climate rule = average daily high temperature per season.

- **Retest:**
  - After changes 5–6, `try_tools.py` from Lisbon: prices almost unchanged (Porto €563 → €561, Madrid €667 → €665, Rome €963 → €964); Seville is now a train (314 km) so it became the cheapest. From Madrid: cities found, Madrid skipped, Lisbon included. Unknown tool and missing field still give the right errors.
  - After change 7 (25 Nov): eval 15/15 messages, 40/40 fields.
  - After changes 8–10 (25 Nov): eval 16/16, 42/42 (gemini-flash-lite-latest); `try_tools.py`: all 30 cities load; from Madrid 16 cities; from Paris works (cheapest Kraków); from Ibiza → clear "not one of our starting cities". From Paris, London is a train (344 km, 3.8 h, €86).

- **Still to do:** update the map in `views/trip_finder.py` to use `travel.py` (waiting for Shaahir's OK), then delete `travel_from` from `schemas.py` and `cities.json`, and `geo.py`.
- **Limitations found:** travel is estimated from straight-line distance (same price both ways, one mode per route); routes under 400 km across the sea (Athens–Mykonos, Dublin–Edinburgh, Split–Rome/Naples/Venice) come out as "train".

### Step 16 – The map uses travel.py and the 30 cities (branch `any-city`)
- **Why:** the map in `views/trip_finder.py` (Shaahir's) still used the old Lisbon-only data: `travel_from` for travel time and `COORDS` from `geo.py` for locations (only 6 cities). After Step 15, `estimate_cost` needs the travel passed in, so the map would give an error, and only 6 of the 30 cities would show.
- **Decision:** small changes in Shaahir's file without waiting for his reply, because they only connect his map to the new code; he reviews them in the pull request before they go into `main`, and I tell him what changed.
- **Planned changes in `views/trip_finder.py`:**
  1. Imports: remove `from geo import COORDS`, add `from travel import travel_between`.
  2. `map_rows` (lines 108–109): `travel = travel_between(by_id[BASELINE.origin], c)` then `estimate = estimate_cost(c, BASELINE, travel)`, instead of `travel_from`.
  3. Line 140: `"lat": c.lat, "lon": c.lon` instead of `COORDS[c.id]`.
  4. Line 184: show every city except the start city (`c.id != BASELINE.origin`) instead of only the cities in `COORDS`.
- **Then:** delete `geo.py`, `travel_from` (in `schemas.py` and `cities.json`) and the old test page `pages/1_Trip_results.py` (it also calls `estimate_cost` with 2 inputs and the app no longer opens it).
- **Changes:** the 4 planned changes in `views/trip_finder.py`, plus:
  - **Bug:** Saw: the map only showed ~11 of 29 cities (central Europe; Spain, Portugal, Greece, Iceland and the Canaries were off screen). Cause: the camera was set by hand (`center` lat 50 / lon 10 + `projection scale 3.2`), which fitted the original 6 cities but not cities from Iceland to the Canaries. Fix: replaced both with `"fitbounds": "locations"`, so the map zooms to fit all the dots (and still works when cities are added or filtered).
  - Note: all dots were yellow under "Your Past Ratings" because the test account had no ratings yet ("no data" = middle colour); not a bug.
  - Note: saving Shaahir's file in VS Code on Windows changed every line ending to CRLF, so Git showed the whole file as changed; switched back to LF so only the real changes show.
- **Retest:** map shows 29 dots (Reykjavik to Las Palmas to Mykonos); Average Price goes green→red; clicking Paris → "Price a trip" gives a card; "From Madrid, somewhere with beaches" gives cards.
  - **Bug found (not fixed, existed before):** Saw: clicked Copenhagen on the map, then chose Paris in "…or choose from the list" → it stayed on Copenhagen. Cause: `city_id = map_pick or list_pick` (views/trip_finder.py) — a map click stays selected and always wins over the list. Not part of any-city; reported to Shaahir.
    - Cleanup: deleted `pages/1_Trip_results.py` (old developer test page, broken and no longer opened) and `travel_from` (schemas.py + all 30 cities; travel is calculated by travel.py). Kept `geo.py` because Shaahir asked to — it is no longer used by the map; asked him in the pull request whether it can go.
    - **Then:** delete `travel_from` (in `schemas.py` and `cities.json`) and the old test page `pages/1_Trip_results.py` (it calls `estimate_cost` with 2 inputs and the app no longer opens it). `geo.py` stays for now (Shaahir asked to keep it).