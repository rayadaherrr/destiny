# Destiny – Data model

## cities.json – one entry per city

| Field | Meaning | Source |
|---|---|---|
| lat, lon | Location of the city centre (west of Greenwich is negative) | Shaahir's geo.py / Google Maps |
| avg_night_price_eur | Price per night for a whole place | Airbnb (Lisbon: Inside Airbnb median, Dec 2025) |
| food_per_day_eur | Food per person per day | estimate |
| activities_per_day_eur | Activities per person per day | estimate |
| climate | Weather per season (see rule below) | average temperatures |
| seasons | Months with higher (high) or lower (low) prices | estimate |

## Climate rule
Average temperature of the season:
- 28 °C or more → **hot**
- 22–27 °C → **warm**
- 15–21 °C → **mild**
- below 15 °C → **cold**
