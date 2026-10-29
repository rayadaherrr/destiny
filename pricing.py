import datetime

from schemas import City, TripEstimate, TripRequest

# Price rules: the same for every city (the months are in cities.json)
SEASON_MULTIPLIER = {"high": 1.3, "normal": 1.0, "low": 0.8}

# (booked at least this many days before the trip, multiplier for travel)
BOOKING_MULTIPLIER = [
    (60, 0.8),
    (21, 1.0),
    (7, 1.3),
    (0, 1.6),
]

DEFAULT_NIGHTS = 5   # used when the user gave no dates


def count_nights(start_date, end_date):
    # 10 June -> 15 June = 5 nights
    return (end_date - start_date).days


def season_of(city: City, month: int):
    # Look the month up in the city's high and low lists; anything else is normal
    if month in city.seasons.high:
        return "high"
    if month in city.seasons.low:
        return "low"
    return "normal"


def booking_multiplier(start_date):
    # How many days between today and the trip decides how expensive travel is
    days_before = (start_date - datetime.date.today()).days
    for min_days, multiplier in BOOKING_MULTIPLIER:
        if days_before >= min_days:
            return multiplier
    return BOOKING_MULTIPLIER[-1][1]   # trip is today or in the past: the most expensive


def estimate_cost(city: City, request: TripRequest):
    # Step 1: how to get there from the user's starting city
    travel = city.travel_from.get(request.origin)
    if travel is None:
        return None   # we have no travel data from this origin to this city

    # Step 2: dates known -> use them; no dates -> a rough estimate with defaults
    if request.start_date and request.end_date:
        nights = count_nights(request.start_date, request.end_date)
        season = season_of(city, request.start_date.month)
        booking = booking_multiplier(request.start_date)
    else:
        nights = DEFAULT_NIGHTS
        season = "normal"
        booking = 1.0

    # Step 3: group size (never 0) and the season multiplier
    people = max(request.people, 1)
    season_mult = SEASON_MULTIPLIER[season]

    # Step 4: every amount is per person, for the whole trip
    travel_eur = travel.cost_eur * 2 * season_mult * booking             # return trip
    stay_eur = city.avg_night_price_eur * season_mult * nights / people  # shared place
    food_eur = city.food_per_day_eur * nights
    activities_eur = city.activities_per_day_eur * nights
    total_eur = travel_eur + stay_eur + food_eur + activities_eur

    # Step 5: fill in the price form
    return TripEstimate(
        city_id=city.id,
        city_name=city.name,
        nights=nights,
        people=people,
        season=season,
        travel_eur=round(travel_eur, 2),
        stay_eur=round(stay_eur, 2),
        food_eur=round(food_eur, 2),
        activities_eur=round(activities_eur, 2),
        total_eur=round(total_eur, 2),
    )