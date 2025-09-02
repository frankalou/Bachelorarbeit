
#Erstellt drei Diagramme zum Hochwasserrisikoanteil der Gebäude in Unterfranken
#nach Gemeinde und Risikoklasse. 

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp
#- data/raster/HSM_WoE_C.tif

#Output:
#- Anzeige der Histogramme im Plot-Fenster


import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint

# === Histogrammerstellung ===

# 1. Shapefile laden
buildings_path = "data/shapefiles/buildings_unterfranken_clipped.shp"
gdf = gpd.read_file(buildings_path)

# 2. MultiPoints aufspalten
def explode_multipoints(gdf):
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

gdf = explode_multipoints(gdf)

# 3. Raster laden und Risiko extrahieren
raster_path = "data/raster/HSM_WoE_C.tif"
with rasterio.open(raster_path) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)
    coords = [(geom.x, geom.y) for geom in gdf.geometry if geom is not None and geom.geom_type == "Point"]
    risiko_values = [val[0] if val[0] != src.nodata else np.nan for val in src.sample(coords)]

# 4. Risiko-Werte zuordnen
gdf = gdf[gdf.geometry.notnull()]
gdf = gdf[gdf.geometry.type == "Point"]
gdf = gdf.iloc[:len(risiko_values)].copy()
gdf["Risiko"] = risiko_values

bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
gdf = gdf.dropna(subset=["Risiko"])
gdf["Risiko_Klasse"] = pd.cut(gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

# 5. Gemeinden und Risikoklassen gruppieren
relevante_klassen = labels_risiko
farben = {
    "sehr gering": "darkgreen",
    "gering": "green",
    "mittel": "gold",
    "hoch": "orange",
    "sehr hoch": "red"
}

risiko_counts = gdf.groupby(["LocalityNa", "Risiko_Klasse"]).size().unstack(fill_value=0)
for rk in relevante_klassen:
    if rk not in risiko_counts.columns:
        risiko_counts[rk] = 0

risiko_counts["gesamt"] = risiko_counts.sum(axis=1)
risiko_prozent = (risiko_counts[relevante_klassen].T / risiko_counts["gesamt"]).T * 100

# 6. Plot erstellen
def plot_risiko_verteilung(risiko_df, sortierung, title_suffix):
    risiko_df_sorted = risiko_df.sort_values(by=sortierung, ascending=False).reset_index()
    x = np.arange(len(risiko_df_sorted))
    y = np.row_stack([risiko_df_sorted[rk].values for rk in relevante_klassen])
    y_stack = np.cumsum(y, axis=0)

    fig, ax = plt.subplots(figsize=(18, 8))

    # Stacked area plot
    for i, rk in enumerate(relevante_klassen):
        bottom = y_stack[i - 1] if i > 0 else np.zeros_like(x)
        ax.fill_between(x, bottom, y_stack[i], label=rk, color=farben[rk])

    # Linien zwischen den Flächen
    for i in range(1, len(relevante_klassen)):
        ax.plot(x, y_stack[i - 1], color="black", linewidth=0.7, linestyle="--", alpha=0.7)

    # Marker-Städte
    marker_staedte = ["Würzburg", "Schweinfurt", "Aschaffenburg"]
    for stadt in marker_staedte:
        try:
            idx = risiko_df_sorted[risiko_df_sorted["LocalityNa"] == stadt].index[0]
            ax.axvline(x=idx, color="black", linestyle="--", linewidth=1)
            ax.text(
                idx, 100, stadt,
                rotation=90, va="top", ha="center", fontsize=9, fontweight="bold", color="black",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=2),
                transform=ax.transData
            )
        except IndexError:
            print(f"{stadt} nicht gefunden!")

    ax.set_xlim(0, len(x) - 1)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Gemeinden (sortiert nach Hochwasserrisikoanteil)")
    ax.set_ylabel("Anteil Hochwasserrisiko (%)")
    ax.set_title(f"Hochwasserrisikoanteil der Gebäude über alle Gemeinden in Unterfranken\n(Gemeinden sortiert nach {title_suffix} Risiko)", fontsize=14, loc="center")

    ax.legend(title="Risikoklasse", loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.show()

# 7. Diagramme plotten
plot_risiko_verteilung(risiko_prozent, "sehr hoch", "sehr hohem")
plot_risiko_verteilung(risiko_prozent, "mittel", "mittlerem")
risiko_prozent["sehr gering + gering"] = risiko_prozent["sehr gering"] + risiko_prozent["gering"]
plot_risiko_verteilung(risiko_prozent, "sehr gering + gering", "sehr geringem und geringem")
