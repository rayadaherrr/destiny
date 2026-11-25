# Destiny – Data model

## cities.json – one entry per city

| Field | Meaning | Source |
|---|---|---|
| lat, lon | Location of the city centre (west of Greenwich is negative) | Shaahir's geo.py / Google Maps |
| avg_night_price_eur | Price per night for a whole place | first 6 cities: Airbnb averages; Lisbon: Inside Airbnb median (Dec 2025); 23 cities added on 25 Nov: estimates (relative price levels) |
| food_per_day_eur | Food per person per day | estimate |
| activities_per_day_eur | Activities per person per day | estimate |
| climate | Weather per season (see rule below) | average daily high temperature of each season |
| seasons | Months with higher (high) or lower (low) prices | estimate |

## Climate rule
Average daily high temperature of the season (spring = Mar–May, summer = Jun–Aug, autumn = Sep–Nov, winter = Dec–Feb):
- 28 °C or more → **hot**
- 22–27 °C → **warm**
- 15–21 °C → **mild**
- below 15 °C → **cold**
