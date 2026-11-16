"""Fill the database with a few demo travellers so there is something to browse.
Run with:  uv run python seed.py
"""
import db

db.init_db()

DEMO = {
    "alex": [("barcelona", 5, "Best tapas of my life. Go hungry."),
             ("rome", 4, "Crowded, but unforgettable.")],
    "marta": [("porto", 5, "Wine cellars and seafood by the river."),
              ("seville", 4, "Too hot in July, perfect in spring.")],
    "joao": [("madrid", 3, "Good museums, nothing special at night."),
             ("valencia", 5, "Beach plus paella. Easy win.")],
}

for username, trips in DEMO.items():
    user_id, error = db.create_user(username, "demo123")
    if user_id is None:
        print(f"skipped {username}: {error}")
        continue
    for city_id, rating, review in trips:
        db.add_trip(user_id, city_id, rating, review)
    print(f"created {username} with {len(trips)} trips")