# Dieser Code wurde einschließlich bis Punkt 6 von John Freisen bereitgestellt

import os
import pandas as pd
import numpy as np
import fiona
import geopandas as gpd
import glob
from shapely.geometry import Point, box

# === 1. Dateipfade ===
input_gml_folder = os.path.join("..", "data", "gml")          # Eingügen der GML-Dateien von Zenodo
output_folder = os.path.join("..", "output")                 # Ergebnisse werden hier gespeichert
raster_file = os.path.join("..", "data", "csv", "unterfranken_polygon.csv")  # CSV Rasterpunkte

# Ordner erstellen, falls sie nicht existieren
os.makedirs(output_folder, exist_ok=True)
os.makedirs(input_gml_folder, exist_ok=True)

# === 2. Alle GMLs einlesen und in Shapefiles umwandeln ===
for filename in os.listdir(input_gml_folder):
    if filename.endswith(".gml"):
        input_gml = os.path.join(input_gml_folder, filename)
        output_shp = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.shp")
        try:
            with fiona.open(input_gml, driver="GML") as input_layer:
                schema = input_layer.schema
                crs = input_layer.crs
                with fiona.open(output_shp, "w", driver="ESRI Shapefile", schema=schema, crs=crs) as output_layer:
                    for feature in input_layer:
                        output_layer.write(feature)
            print(f"Conversion completed: {filename} -> {os.path.basename(output_shp)}")
        except Exception as e:
            print(f"Fehler beim Verarbeiten von {filename}: {e}")

print("All GML files have been converted to Shapefiles.")

# === 3. Shapefiles einlesen ===
gdf_list = []
for shp_file in glob.glob(os.path.join(output_folder, "*.shp")):
    try:
        gdf = gpd.read_file(shp_file)
        gdf_list.append(gdf)
    except Exception as e:
        print(f"Fehler beim Einlesen von {shp_file}: {e}")

if not gdf_list:
    raise ValueError("Keine Shapefiles gefunden oder einlesbar!")

buildings_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=gdf_list[0].crs)

# === 4. Gebäude filtern ===
residential_codes = ["31001_1000", "31001_9998"]
if "function" not in buildings_gdf.columns:
    raise KeyError("Spalte 'function' nicht gefunden!")
gdf_res = buildings_gdf[buildings_gdf["function"].isin(residential_codes)].copy()

# === 5. Höhe/Stockwerke und Volumen berechnen ===
valid = gdf_res.dropna(subset=["measuredHe", "storeysAbo"]).copy()
valid["storeyHei"] = valid["measuredHe"] / valid["storeysAbo"]
mean_storey_height = valid["storeyHei"].mean()

gdf_res["est_storeys"] = gdf_res["storeysAbo"]
gdf_res["est_storeys"] = np.where(
    gdf_res["storeysAbo"].isna(),
    gdf_res["measuredHe"] / mean_storey_height,
    gdf_res["storeysAbo"]
)
gdf_res["est_storeys"] = gdf_res["est_storeys"].round()
gdf_res["area"] = gdf_res.geometry.area
gdf_res["floorArea"] = gdf_res["area"] * gdf_res["est_storeys"]
gdf_res["volume"] = gdf_res["area"] * gdf_res["measuredHe"]

# === 6. Reprojektion und Zentroid berechnen ===
gdf_res = gdf_res.to_crs("EPSG:25832")
gdf_res["geometry"] = gdf_res.centroid

# === 7. Raster einlesen und auf EPSG:25832 bringen ===
df_raster = pd.read_csv(raster_file, sep=";")
gdf_raster = gpd.GeoDataFrame(
    df_raster,
    geometry=[Point(x, y) for x, y in zip(df_raster["x_mp_100m"], df_raster["y_mp_100m"])],
    crs="EPSG:3035"
).to_crs(25832)

# Raster-Polygone erzeugen
def make_box(center, size=100):
    x, y = center.x, center.y
    half = size / 2
    return box(x - half, y - half, x + half, y + half)

gdf_raster["geometry"] = gdf_raster.geometry.apply(make_box)

# === 8. Räumlicher Join ===
joined = gpd.sjoin(gdf_res, gdf_raster, how="left", predicate="within")

# === 9. Volumensumme pro Rasterzelle berechnen ===
sum_vol_per_raster = joined.groupby("GITTER_ID_100m")["volume"].sum().rename("sum_volume")
joined = joined.join(sum_vol_per_raster, on="GITTER_ID_100m")

# === 10. Einwohner auf Gebäude verteilen ===
joined["geb_bewohner"] = (joined["volume"] / joined["sum_volume"]) * joined["Einwohner"]

# === 11. Output speichern ===
output_shapefiles_folder = os.path.join("..", "outputs", "shapefiles")
os.makedirs(output_shapefiles_folder, exist_ok=True)

output_shp = os.path.join(output_shapefiles_folder, "buildingsunterfranken.shp")
final = joined[[
    "geometry", "gml_id", "creationDa", "Gemeindesc", "LocalityNa",
    "Thoroughfa", "function", "volume", "geb_bewohner"
]].copy()
final = final.set_crs("EPSG:25832")
final.to_file(output_shp)


print(f"Shapefile gespeichert: {output_shp}")
