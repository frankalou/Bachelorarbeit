import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
import os

# === INPUT SETUP ===
shapefile_path = "data/shapefiles/buildings_unterfranken.shp"
raster_path = "data/raster/HSM_WoE_C.tif"
output_dir = "outputs/shapefiles"
os.makedirs(output_dir, exist_ok=True)

# Ausgabeordner für Ergebnisse
output_shapefile = os.path.join(output_dir, "top20_gemeinden_unterfranken_risiko.shp")

# === 1. Datei einlesen ===
gdf = gpd.read_file(shapefile_path)

# === 2. Raster einlesen und Risiko extrahieren
with rasterio.open(raster_path) as src:
    # reprojizieren, falls nötig
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    risiko_values = [val[0] if val[0] != src.nodata else np.nan for val in src.sample(coords)]

# Risiko-Werte zum GeoDataFrame hinzufügen
gdf["Risiko"] = risiko_values

# === 3. Risikoklassen zuordnen ===
bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

gdf = gdf.dropna(subset=["Risiko"])  # nur gültige Werte behalten
gdf["Risiko_Klasse"] = pd.cut(gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

# === 4. Risikostatistik pro Gemeinde berechnen ===
# Gebäude pro Gemeinde + Risiko-Klasse zählen
risiko_counts = gdf.groupby(["LocalityNa", "Risiko_Klasse"]).size().unstack(fill_value=0)

# fehlende Klassen ergänzen
for rk in labels_risiko:
    if rk not in risiko_counts.columns:
        risiko_counts[rk] = 0

# Anteil "hoch" + "sehr hoch"
risiko_counts["hoch_total"] = risiko_counts["hoch"] + risiko_counts["sehr hoch"]
risiko_counts["gesamt"] = risiko_counts[labels_risiko].sum(axis=1)
risiko_counts["hoch_anteil"] = risiko_counts["hoch_total"] / risiko_counts["gesamt"]

# Top 20 Gemeinden nach hohem Risiko
top20_hoch = risiko_counts.sort_values(by="hoch_anteil", ascending=False).head(20)

# Anteil "sehr gering" + "gering"
risiko_counts["niedrig_total"] = risiko_counts["sehr gering"] + risiko_counts["gering"]
risiko_counts["niedrig_anteil"] = risiko_counts["niedrig_total"] / risiko_counts["gesamt"]

# Top 20 Gemeinden nach niedrigem Risiko
top20_niedrig = risiko_counts.sort_values(by="niedrig_anteil", ascending=False).head(20)

# === 5. Geometrie der "Top"-Gemeinden bestimmen ===
gemeinden_hoch = top20_hoch.index.tolist()
gemeinden_niedrig = top20_niedrig.index.tolist()

# nur gültige Gebäude behalten
gdf_valid = gdf.dropna(subset=["Risiko_Klasse", "LocalityNa"])

# Schwerpunktpunkte pro Gemeinde
gemeinde_dissolved = gdf_valid.dissolve(by="LocalityNa", as_index=False)
gemeinde_centroids = gemeinde_dissolved.centroid
gemeinde_punkte = gpd.GeoDataFrame({
    "LocalityNa": gemeinde_dissolved["LocalityNa"],
    "geometry": gemeinde_centroids
}, crs=gdf.crs)

# Top-Gemeinden herausfiltern
punkte_hoch = gemeinde_punkte[gemeinde_punkte["LocalityNa"].isin(gemeinden_hoch)]
punkte_niedrig = gemeinde_punkte[gemeinde_punkte["LocalityNa"].isin(gemeinden_niedrig)]

# Risikogruppen kennzeichnen
punkte_hoch["risikogruppe"] = "hoch"
punkte_niedrig["risikogruppe"] = "niedrig"

# Kombination
punkte_gesamt = pd.concat([punkte_hoch, punkte_niedrig])
punkte_gesamt = gpd.GeoDataFrame(punkte_gesamt, geometry="geometry", crs=gdf.crs)

# === 6. Ergebnis speichern ===
punkte_gesamt.to_file(output_shapefile, driver="ESRI Shapefile")
print(f"Shapefile gespeichert unter: {output_shapefile}")