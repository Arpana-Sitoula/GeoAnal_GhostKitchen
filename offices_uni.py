import osmnx as ox
import geopandas as gpd

# ── Universities ─────────────────────────────────────────────────────────────
print("Downloading university polygons...")
universities = ox.features_from_place(
    "Frankfurt am Main, Germany",
    tags={"amenity": ["university", "college", "campus"]}
)

# Keep only polygons
universities = universities[
    universities.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()

# Estimate population: 1 student per 80m² of campus
universities["area_m2"] = universities.geometry.to_crs("EPSG:3857").area
universities["estimated_pop"] = (universities["area_m2"] / 80).astype(int)

# Keep only useful columns
universities = universities[["geometry", "name", "area_m2", "estimated_pop"]].copy()

print(f"Universities found: {len(universities)}")
print(universities[["name", "area_m2", "estimated_pop"]].to_string())
universities.to_file("frankfurt_universities.gpkg", driver="GPKG")
print("Saved frankfurt_universities.gpkg\n")

# ── Offices ──────────────────────────────────────────────────────────────────
print("Downloading office polygons...")
offices = ox.features_from_place(
    "Frankfurt am Main, Germany",
    tags={"building": "office"}
)

# Keep only polygons
offices = offices[
    offices.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()

# Estimate population: 1 worker per 25m² of office space
offices["area_m2"] = offices.geometry.to_crs("EPSG:3857").area
offices["estimated_pop"] = (offices["area_m2"] / 25).astype(int)

# Keep only useful columns
offices = offices[["geometry", "name", "area_m2", "estimated_pop"]].copy()

print(f"Offices found: {len(offices)}")
print(offices[["name", "area_m2", "estimated_pop"]].head(10).to_string())
offices.to_file("frankfurt_offices.gpkg", driver="GPKG")
print("Saved frankfurt_offices.gpkg\n")

print("All POIs downloaded and saved!")