import osmnx as ox

print("Downloading restaurants and food places...")
# This grabs standard restaurants, fast food, food courts, and cafes
restaurants = ox.features_from_place(
    "Frankfurt am Main, Germany",
    tags={"amenity": ["restaurant", "fast_food", "food_court", "cafe"]}
)

# Optional: If you want to explicitly look for commercial/cloud kitchens 
# OSM sometimes uses industrial/commercial tags for them, but 'amenity' covers where people eat.

restaurants.to_file("frankfurt_restaurants.gpkg", driver="GPKG")
print(f"Saved {len(restaurants)} restaurants and food places")