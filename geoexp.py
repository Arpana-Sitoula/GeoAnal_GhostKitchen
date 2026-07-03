import geopandas as gpd
import requests
import numpy as np
from shapely.geometry import shape
import time

# ── Step 1: Load Frankfurt kitchen candidate points ──────────────────────────
print("Loading Frankfurt population data...")
frankfurt = gpd.read_file("frankfurt_population.gpkg")
frankfurt = frankfurt.to_crs("EPSG:4326")

# ── Step 2: Load wider region population (fixes border blind spot) ───────────
print("Loading wider region population...")
gdf = gpd.read_file("kontur_population_DE_20231101.gpkg")
gdf = gdf.to_crs("EPSG:4326")
wider_population = gdf.cx[8.20:9.10, 49.80:50.45]
print(f"Wider region hexes: {len(wider_population)}")

# ── Step 3: Load POIs with estimated populations ─────────────────────────────
print("Loading POIs...")
universities = gpd.read_file("frankfurt_universities.gpkg")
offices = gpd.read_file("frankfurt_offices.gpkg")
universities = universities.to_crs("EPSG:4326")
offices = offices.to_crs("EPSG:4326")

print(f"Universities: {len(universities)}")
print(f"Offices: {len(offices)}")

# ── Step 4: Precompute accurate centroids ────────────────────────────────────
print("Computing centroids...")
frankfurt["centroid"] = (
    frankfurt.geometry.to_crs("EPSG:3857")
    .centroid.to_crs("EPSG:4326")
)
wider_population["centroid"] = (
    wider_population.geometry.to_crs("EPSG:3857")
    .centroid.to_crs("EPSG:4326")
)
universities["centroid"] = (
    universities.geometry.to_crs("EPSG:3857")
    .centroid.to_crs("EPSG:4326")
)
offices["centroid"] = (
    offices.geometry.to_crs("EPSG:3857")
    .centroid.to_crs("EPSG:4326")
)

# Kitchen candidates = all Frankfurt hex centroids
kitchen_points = list(frankfurt["centroid"])
print(f"Candidate kitchen points: {len(kitchen_points)}")

GEOAPIFY_API_KEY = "48c7b94cc3dd4045b13683902704854f"

# ── Step 5: Isochrone function (bicycle, 10 min) ─────────────────────────────
def get_isochrone(lon, lat, minutes=10):
    url = "https://api.geoapify.com/v1/isoline"
    params = {
        "lat": lat,
        "lon": lon,
        "type": "time",
        "mode": "bicycle",
        "range": minutes * 60,
        "apiKey": GEOAPIFY_API_KEY
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        features = r.json().get("features", [])
        if features:
            return shape(features[0]["geometry"])
    else:
        print(f"  Error {r.status_code}: {r.text}")
    return None

# ── Step 6: Calculate DRS for each kitchen point ─────────────────────────────
results = []
for i, pt in enumerate(kitchen_points):
    print(f"Point {i+1}/{len(kitchen_points)} → ({pt.y:.4f}, {pt.x:.4f})")

    iso = get_isochrone(pt.x, pt.y, minutes=10)
    if iso is None:
        print("  Skipped")
        continue

    # Residential population from wider region
    pop_inside = wider_population[wider_population["centroid"].within(iso)]
    residential_pop = int(pop_inside["population"].sum())

    # University estimated population inside isochrone
    uni_inside = universities[universities["centroid"].within(iso)]
    uni_pop = int(uni_inside["estimated_pop"].sum())

    # Office estimated population inside isochrone
    off_inside = offices[offices["centroid"].within(iso)]
    off_pop = int(off_inside["estimated_pop"].sum())

    # Raw weighted demand (same unit — estimated people)
    weighted_demand = (
        0.60 * residential_pop + #order= weekdays+weekends /higher order from this category
        0.15 * uni_pop +  #order=weekends (2 days) / lower orders
        0.25 * off_pop #order=weekdays (5 days) / medium orders
    )

    print(f"  Residential: {residential_pop:,} | "
          f"Uni pop: {uni_pop:,} | "
          f"Office pop: {off_pop:,} | "
          f"Weighted: {weighted_demand:,.0f}")

    results.append({
        "geometry": pt,
        "residential_pop": residential_pop,
        "uni_pop": uni_pop,
        "off_pop": off_pop,
        "weighted_demand": int(weighted_demand),
        "lon": round(pt.x, 5),
        "lat": round(pt.y, 5)
    })

    time.sleep(1)


# ── Step 7: Save ─────────────────────────────────────────────────────────────
import pandas as pd

df = pd.DataFrame(results)
drs_gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
drs_gdf.to_file("frankfurt_drs.gpkg", driver="GPKG")

print(f"\nDone! {len(drs_gdf)} kitchen locations scored")
print("\nTop 10 locations by weighted demand:")
print(drs_gdf[["lat", "lon", "residential_pop", "uni_pop",
               "off_pop", "weighted_demand"]]
      .sort_values("weighted_demand", ascending=False)
      .head(10).to_string())