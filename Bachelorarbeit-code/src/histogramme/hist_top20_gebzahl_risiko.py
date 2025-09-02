
#Analyse der Top-20 gebäudereichsten Gemeinden nach Hochwasserrisiko.

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp   
#- data/raster/HSM_WoE_C.tif                            

#Output:
#- Anzeige des Plots im Fenster

import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint

# === 1. MultiPoints aufspalten ===

def explode_multipoints(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Zerlegt MultiPoint-Geometrien in einzelne Punkte."""
    rows = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if isinstance(geom, Point):
            rows.append(row)
        elif isinstance(geom, MultiPoint):
            for pt in geom.geoms:
                new_row = row.copy()
                new_row.geometry = pt
                rows.append(new_row)
    return gpd.GeoDataFrame(rows, crs=gdf.crs)

# === 2. Diagramm erstellen ===

# 1. Daten laden
shapefile_path = "data/shapefiles/buildings_unterfranken_clipped.shp"
raster_path = "data/raster/HSM_WoE_C.tif"

gdf = gpd.read_file(shapefile_path)
gdf = explode_multipoints(gdf)

with rasterio.open(raster_path) as src:
    # reprojizieren, falls nötig
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    risiko_values = [
        val[0] if val[0] != src.nodata else np.nan
        for val in src.sample(coords)
    ]

gdf["Risiko"] = risiko_values

# 2. Risikoklassen bilden
bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

gdf = gdf.dropna(subset=["Risiko"])
gdf["Risiko_Klasse"] = pd.cut(
    gdf["Risiko"],
    bins=bins_risiko,
    labels=labels_risiko,
    include_lowest=True
)

# Farbzuordnung
farben = {
    "sehr gering": "darkgreen",
    "gering": "green",
    "mittel": "gold",
    "hoch": "orange",
    "sehr hoch": "red"
}
schriftfarben = {
    "sehr gering": "white",
    "gering": "white",
    "mittel": "black",
    "hoch": "black",
    "sehr hoch": "black"
}
risiko_klassen = labels_risiko

# 3. Top 20 Gemeinden berechnen
top20_gemeinden = gdf["LocalityNa"].value_counts().head(20).index
gdf_top = gdf[gdf["LocalityNa"].isin(top20_gemeinden)]

gruppen = gdf_top.groupby(
    ["LocalityNa", "Risiko_Klasse"]
).size().unstack(fill_value=0)

gruppen = gruppen[risiko_klassen]  
prozent_df = (gruppen.T / gruppen.sum(axis=1)).T * 100

# Sortieren nach Gesamtgebäudeanzahl
gesamtanzahl = gruppen.sum(axis=1)
prozent_df = prozent_df.loc[gesamtanzahl.sort_values(ascending=False).index]

# 4. Diagramm zeichnen
fig, ax = plt.subplots(figsize=(14, 8))

prozent_df.plot(
    kind="bar",
    stacked=True,
    color=[farben[r] for r in risiko_klassen],
    ax=ax
)

# Prozentwerte in Balken schreiben
for i, (idx, row) in enumerate(prozent_df.iterrows()):
    y_offset = 0
    for risiko in risiko_klassen:
        wert = row[risiko]
        if pd.notna(wert) and wert > 1:
            ax.text(
                i, y_offset + wert / 2,
                f"{wert:.0f}%",
                ha="center", va="center",
                color=schriftfarben[risiko],
                fontsize=8,
                fontweight="bold"
            )
        y_offset += wert

# Layout und Achsen
ax.set_title("Top 20 der gebäudereichsten Gemeinden nach Hochwasserrisiko", fontsize=16)
ax.set_xlabel("Gemeinde")
ax.set_ylabel("Anteil in %")
ax.set_ylim(0, 100)
ax.legend(title="Hochwasserrisiko", bbox_to_anchor=(1.05, 1), loc="upper left")
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
plt.tight_layout()
plt.show()
