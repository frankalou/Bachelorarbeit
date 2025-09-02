import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
import os

# === 1. Daten einlesen ===
gdf_gemeinden = gpd.read_file("data/shapefiles/VG5000_GEM.shp")
gdf_unterfranken = gpd.read_file("data/shapefiles/Unterfranken.shp")

# === 2. CRS anpassen ===
gdf_gemeinden = gdf_gemeinden.to_crs(gdf_unterfranken.crs)

# === 3. Gesamtflächen der Gemeinden berechnen (Originallayer) ===
gdf_gemeinden["area_total"] = gdf_gemeinden.geometry.area

# === 4. Gemeinden auf Unterfranken clippen (Schnittfläche) ===
gdf_uf_gemeinden = gpd.overlay(gdf_gemeinden, gdf_unterfranken, how="intersection")

# === 5. Flächen der Schnittfläche berechnen ===
gdf_uf_gemeinden["area_intersect"] = gdf_uf_gemeinden.geometry.area

# === 6. Join der Gesamtflächen ===
area_total_df = gdf_gemeinden[["GEN", "area_total"]].set_index("GEN")
gdf_uf_gemeinden = gdf_uf_gemeinden.set_index("GEN").join(area_total_df, rsuffix="_total")

# === 7. Flächenanteil berechnen ===
gdf_uf_gemeinden["overlap_ratio"] = (
    gdf_uf_gemeinden["area_intersect"] / gdf_uf_gemeinden["area_total_total"]
)

# === 8. Gemeinden filtern (≥ 60% in Unterfranken) ===
gdf_uf_gemeinden_filtered = gdf_uf_gemeinden[gdf_uf_gemeinden["overlap_ratio"] > 0.6].reset_index()

# === 9. Raster einlesen ===
raster_path = "data/raster/HSM_WoE_C.tif"
raster = rasterio.open(raster_path)
raster_array = raster.read(1)

# === 10. Risiko-Klassen definieren ===
bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

# === 11. Klassifizierung der Rasterwerte ===
raster_classified = np.digitize(raster_array, bins=bins_risiko)

# === 12. Raster temporär speichern ===
classified_tif_path = "output/raster_classified.tif"
os.makedirs("output", exist_ok=True)

with rasterio.open(
    classified_tif_path,
    "w",
    driver="GTiff",
    height=raster_classified.shape[0],
    width=raster_classified.shape[1],
    count=1,
    dtype=raster_classified.dtype,
    crs=raster.crs,
    transform=raster.transform,
    nodata=0,
) as dst:
    dst.write(raster_classified, 1)

# === 13. Zonenstatistik ===
stats = zonal_stats(
    gdf_uf_gemeinden_filtered,
    classified_tif_path,
    stats="count",
    categorical=True,
    nodata=0,
)
df_stats = pd.DataFrame(stats)

# === 14. Risiko-Spalten umbenennen ===
label_map = {i + 1: labels_risiko[i] for i in range(len(labels_risiko))}
df_stats.rename(columns=label_map, inplace=True)

# Fehlende Klassen ergänzen
for label in labels_risiko:
    if label not in df_stats.columns:
        df_stats[label] = 0

# === 15. Mit Geometrien kombinieren ===
result = pd.concat([gdf_uf_gemeinden_filtered[["GEN", "geometry"]], df_stats], axis=1)

# === 16. Prozentanteile berechnen ===
result["gesamt"] = result[labels_risiko].sum(axis=1)
for label in labels_risiko:
    result[f"{label}_pct"] = (result[label] / result["gesamt"]) * 100

# === 17. Spaltennamen anpassen ===
result = result.rename(
    columns={
        "sehr gering_pct": "s_ger_pct",
        "gering_pct": "ger_pct",
        "mittel_pct": "mit_pct",
        "hoch_pct": "hoch_pct",
        "sehr hoch_pct": "s_hoch_pct",
    }
)

# === 18. Ergebnis speichern ===
output_folder = "outputs/shapefiles"
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "flaechen_gemeinden_risiko_unterfranken.shp")

result_gdf = gpd.GeoDataFrame(result, geometry="geometry", crs=gdf_uf_gemeinden_filtered.crs)
result_gdf.to_file(output_path)

print("Shapefile mit gefilterten Gemeinden gespeichert:", output_path)