
# Drei Heatmaps, die den Gebäudeanteil pro Haushaltsgröße und Hochwasserrisiko
# für Aschaffenburg, Schweinfurt und Würzburg darstellen

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp
#- data/raster/HSM_WoE_C.tif 

#Output:
#- Anzeige des Histogramms im Plot-Fenster

import geopandas as gpd
import rasterio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Eingabedaten
shapefile_path = "../data/shapefiles/buildings_unterfranken_clipped.shp"
raster_path = "../data/raster/HSM_WoE_C.tif"

# === Histogramm erstellen ===

# 1. Shapefile laden und Risiko aus Raster extrahieren
gdf = gpd.read_file(shapefile_path)

with rasterio.open(raster_path) as src:
    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    risiko_values = [val[0] if val else None for val in src.sample(coords)]

gdf["Risiko"] = risiko_values
gdf = gdf.dropna(subset=["Risiko", "geb_bewohn"])
gdf = gdf[(gdf["geb_bewohn"] > 0) & (gdf["geb_bewohn"] <= 200)]

# 2. Klasseneinteilung
bins_risiko = [-18.459, -11, -7, -2.6, 2.5, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
gdf["Risiko_Klasse"] = pd.cut(gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

bins_bewohner = [0, 2, 5, 10, 20, 50, 100, float("inf")]
labels_bewohner = ["1–2", "3–5", "6–10", "11–20", "21–50", "51–100", "100+"]
gdf["Bewohner_Klasse"] = pd.cut(gdf["geb_bewohn"], bins=bins_bewohner, labels=labels_bewohner, include_lowest=True)

# 3. Heatmap-Erstellung
staedte = ["Aschaffenburg", "Würzburg", "Schweinfurt"]

for stadt in staedte:
    df_stadt = gdf[gdf["LocalityNa"] == stadt]

    heatmap_data = df_stadt.groupby(["Bewohner_Klasse", "Risiko_Klasse"], observed=False).size().unstack(fill_value=0)
    heatmap_percent = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100
    heatmap_percent = heatmap_percent.reindex(index=labels_bewohner[::-1])  # y-Achse umdrehen

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        heatmap_percent,
        annot=True,
        fmt=".1f",
        cmap="rocket_r",
        linewidths=0.5,
        linecolor='gray',
        cbar_kws={'label': 'Anteil in %'}
    )
    plt.xlabel("Hochwasserrisiko")
    plt.ylabel("Bewohner pro Gebäude (Klassen)")
    plt.title(f"{stadt}: Gebäudeanteile nach Risiko- und Haushaltsgröße")
    plt.tight_layout()
    plt.show()
