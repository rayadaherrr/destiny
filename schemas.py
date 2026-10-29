import datetime
from typing import Literal

from pydantic import BaseModel, Field


Tag = Literal["food", "beach", "nightlife", "culture", "architecture", "nature"]
Mode = Literal["train", "bus", "flight"]
Weather = Literal["hot", "warm", "mild", "cold"]


class Travel(BaseModel):
    hours: float = Field(description="Travel time in hours, one way")
    cost_eur: float = Field(description="Typical one-way price in euros")
    mode: Mode


class Climate(BaseModel):
    spring: Weather
    summer: Weather
    autumn: Weather
    winter: Weather


class Seasons(BaseModel):
    high: list[int] = Field(description="Months (1-12) when prices are higher")
    low: list[int] = Field(description="Months (1-12) when prices are lower")


class City(BaseModel):
    id: str
    name: str
    country: str
    description: str
    avg_night_price_eur: float = Field(description="Average Airbnb price per night for the whole place, in euros")
    food_per_day_eur: float = Field(description="Food cost per person per day, in euros")
    activities_per_day_eur: float = Field(description="Activities cost per person per day, in euros")
    travel_from: dict[str, Travel] = Field(description="Travel to this city, by starting city id")
    tags: list[Tag]
    climate: Climate
    seasons: Seasons


class TripRequest(BaseModel):
    origin: str = Field(description="Starting city id, lowercase. Use 'lisbon' if the user did not say")
    start_date: datetime.date | None = Field(description="First day of the trip, or null if the user gave no date")
    end_date: datetime.date | None = Field(description="Last day of the trip, or null if the user gave no end date")
    people: int = Field(description="How many people are travelling, including the user. Use 1 if not said")
    budget_per_person_eur: float | None = Field(description="Maximum total spend per person in euros, or null if not given")
    max_travel_hours: float | None = Field(description="Maximum one-way travel time in hours, or null if not given")
    destination: str | None = Field(description="City id the user wants to go to, e.g. 'paris' or 'rome' (lowercase, typos corrected), or null if they did not name one")
    interests: list[Tag] = Field(description=(
        "What the user wants from the trip, from the allowed tags. Empty list if nothing was said. "
        "food = restaurants, eating, local cuisine. "
        "nightlife = bars, clubs, going out. "
        "beach = beaches, sea, swimming. "
        "culture = museums, history, art. "
        "architecture = buildings, monuments. "
        "nature = hiking, parks, mountains."
    ))
    climate_wanted: Weather | None = Field(description="Weather the user asked for, e.g. 'somewhere warm' -> warm, or null")
    cheaper_than: str | None = Field(description="City id the trip should be cheaper than, e.g. 'barcelona', or null")



class Turn(BaseModel):
    """One message in the chat history: what the user typed + what Gemini understood."""
    message: str = Field(description="What the user typed")
    request: TripRequest = Field(description="What Gemini understood, or the user's correction")

class TripEstimate(BaseModel):
    city_id: str
    city_name: str
    nights: int = Field(description="Number of nights of the trip")
    people: int = Field(description="Number of people sharing the trip")
    season: Literal["high", "normal", "low"] = Field(description="Price season of the trip's start month")
    travel_eur: float = Field(description="Return travel cost per person, in euros")
    stay_eur: float = Field(description="Accommodation cost per person for the whole trip, shared place")
    food_eur: float = Field(description="Food cost per person for the whole trip")
    activities_eur: float = Field(description="Activities cost per person for the whole trip")
    total_eur: float = Field(description="Total estimated cost per person, in euros")