"""
Destiny's tools: what the agent may call, and the only place they run.

Built on the course's Week 5 tools.py, with the same shape:
- each tool has an argument model (Pydantic), whose JSON Schema is what the model reads;
- run_tool() is the only place a tool runs, and every failure comes back as a result;
- a tool that destroys data asks the user first, in code.
"""
import datetime
import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from pricing import estimate_cost
from schemas import City, TripRequest

CITIES_FILE = Path(__file__).parent / "data" / "cities.json"


def load_cities():
    with open(CITIES_FILE, encoding="utf-8") as f:
        return [City.model_validate(c) for c in json.load(f)]


# ---------------------------------------------------------------- business rules
def fix_year(request):
    """A trip can't start in the past: move it one year forward (a rule in code, Week 5)."""
    today = datetime.date.today()
    start, end = request.start_date, request.end_date
    while start and start < today:
        start = start.replace(year=start.year + 1)
        end = end.replace(year=end.year + 1) if end else None
    return request.model_copy(update={"start_date": start, "end_date": end})




def check(request):
    """Rules checked in code after the model has filled in the arguments (Week 3)."""
    today = datetime.date.today()
    problems = []
    if request.people < 1:
        problems.append("people must be at least 1")
    if request.budget_per_person_eur is not None and request.budget_per_person_eur <= 0:
        problems.append("budget is not positive")
    if (request.start_date is None) != (request.end_date is None):
        problems.append("give both dates, or neither")
    if request.start_date and request.end_date:
        if request.end_date < request.start_date:
            problems.append("the end date is before the start date")
        if request.start_date < today:
            problems.append("the start date is in the past")
    return problems


# ---------------------------------------------------------------- tools

def find_trips(args):
    """Price every city for this request, keep the ones that match, cheapest first."""
    args = fix_year(args)          # ← new: the same rule as in extraction.py
    problems = check(args)
    if problems:
        # Like the teacher's add_expense: say what is wrong, and do not let the agent bend the user's facts
        return {"found": False, "problems": problems,
                "what_to_do": "Nothing was searched. Tell the user what is wrong and ask them to correct it. "
                              "Do not change what they said to make it pass."}

    cities = load_cities()
    by_id = {city.id: city for city in cities}

    if args.destination and args.destination not in by_id:
        return {"found": False, "problems": [f"{args.destination} is not one of our cities yet"],
                "our_cities": sorted(by_id),
                "what_to_do": "Tell the user we do not cover that city yet, and offer the cities we have."}

    # "Cheaper than Barcelona": price Barcelona first, then keep only cities below it
    limit = None
    if args.cheaper_than in by_id:
        reference = estimate_cost(by_id[args.cheaper_than], args)
        limit = reference.total_eur if reference else None

    trips = []
    for city in cities:
        if args.destination and city.id != args.destination:
            continue
        if city.id == args.cheaper_than:
            continue
        estimate = estimate_cost(city, args)
        if estimate is None:                      # no travel data from this starting city
            continue
        travel = city.travel_from[args.origin]
        if args.max_travel_hours is not None and travel.hours > args.max_travel_hours:
            continue
        if limit is not None and estimate.total_eur >= limit:
            continue
        if args.interests and not set(args.interests) & set(city.tags):
            continue
        fits = None if args.budget_per_person_eur is None else estimate.total_eur <= args.budget_per_person_eur
        trips.append({**estimate.model_dump(), "travel_hours": travel.hours, "travel_mode": travel.mode,
                      "tags": city.tags, "fits_budget": fits})

    trips.sort(key=lambda trip: trip["total_eur"])
    if not trips:
        return {"found": False, "trips": [],
                "what_to_do": "No city matches every limit. Tell the user which limit ruled them out, "
                              "and suggest relaxing one."}
    return {"found": True, "trips": trips}

# ---------------------------------------------------------------- the tool list (from the teacher's Week 5 tools.py)

# name: (argument model, function, description). The declarations are built from it.
TOOLS = {
    "find_trips": (TripRequest, find_trips,
                   "Find and price trips from the user's starting city: every city we cover that matches their "
                   "dates, group size, budget, maximum travel time, interests, destination and 'cheaper than' city, "
                   "cheapest first. Use it whenever the user asks where to go or how much a trip would cost."),
}

# Tools that destroy what the user already has. They receive confirm() and must get a yes before acting.
ASK_FIRST = set()   # delete_trip goes here in Part 3

DECLARATIONS = [
    {"type": "function", "name": name, "description": description, "parameters": model.model_json_schema()}
    for name, (model, _, description) in TOOLS.items()
]


def run_tool(name, arguments, confirm):
    """Run one call the model asked for. Every failure comes back as a result; nothing raises."""
    if name not in TOOLS:
        return {"error": f"There is no tool called {name}. The tools are: {', '.join(TOOLS)}."}
    model, function, _ = TOOLS[name]
    try:
        args = model.model_validate(arguments)
    except ValidationError as error:
        problem = error.errors()[0]
        field = ".".join(str(part) for part in problem["loc"]) or "arguments"
        return {"error": f"Invalid {field}: {problem['msg']}. Fix it and call again."}
    try:
        result = function(args, confirm) if name in ASK_FIRST else function(args)
    except Exception as error:
        # A write that failed half-way may or may not have changed the data. Say so,
        # or the agent will repeat it blindly and write it twice.
        return {"error": f"{name} failed: {str(error).rstrip('.')}. If it writes, it may or may not "
                         "have changed the data: read the data again before repeating it."}
    # The API takes a dict of JSON values: wrap anything else, and turn dates into text.
    if not isinstance(result, dict):
        result = {"result": result}
    return json.loads(json.dumps(result, default=str))