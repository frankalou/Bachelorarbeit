
#Analyse von Gebäuden nach Hochwasserrisiko in Unterfranken.

#Dieses Skript erzeugt Balkendiagramme für die Top-20 Gemeinden,
#entweder nach höchstem Anteil von Gebäuden mit hohem Risiko
#oder nach höchstem Anteil mit niedrigem Risiko.

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp   
#- data/raster/HSM_WoE_C.tif                            

#Output:
#- Anzeige des Histogramms im Plot-Fenster

import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint

# 1. Eingabedaten
shapefile_path = "../data/shapefiles/buildings_unterfranken_clipped.shp"
raster_path = "../data/raster/HSM_WoE_C.tif"

# === 1. Multipoints aufspalten ===
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

# === 2. Histogramm erstellen ===

def lade_gebaeude_mit_risiko(shapefile_path, raster_path):
    gdf = gpd.read_file(shapefile_path)
    gdf = explode_multipoints(gdf)

    with rasterio.open(raster_path) as src:
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)

        coords = [(geom.x, geom.y) for geom in gdf.geometry]
        risiko_values = [
            val[0] if val[0] != src.nodata else np.nan
            for val in src.sample(coords)
        ]

    gdf["Risiko"] = risiko_values

    # Risikoklassen definieren
    bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

    gdf = gdf.dropna(subset=["Risiko"])
    gdf["Risiko_Klasse"] = pd.cut(
        gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True
    )
    return gdf

def erstelle_plot(gdf, modus="hoch"):
    """
    Diagramm erstellen.
    modus = "hoch" → Top 20 nach hohem Risiko
    modus = "niedrig" → Top 20 nach niedrigem Risiko
    """
    relevante_klassen = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
    risiko_counts = gdf.groupby(["LocalityNa", "Risiko_Klasse"]).size().unstack(fill_value=0)

    for rk in relevante_klassen:
        if rk not in risiko_counts.columns:
            risiko_counts[rk] = 0

    risiko_counts["gesamt"] = risiko_counts[relevante_klassen].sum(axis=1)

    if modus == "hoch":
        risiko_counts["hoch_total"] = risiko_counts["hoch"] + risiko_counts["sehr hoch"]
        risiko_counts["anteil"] = risiko_counts["hoch_total"] / risiko_counts["gesamt"]
        titel = "Top 20 Gemeinden mit dem höchsten Hochwasserrisiko"
    elif modus == "niedrig":
        risiko_counts["niedrig_total"] = risiko_counts["sehr gering"] + risiko_counts["gering"]
        risiko_counts["anteil"] = risiko_counts["niedrig_total"] / risiko_counts["gesamt"]
        titel = "Top 20 Gemeinden mit dem niedrigsten Hochwasserrisiko"
    else:
        raise ValueError("Ungültiger Modus. Nutze 'hoch' oder 'niedrig'.")

    top20 = risiko_counts.sort_values(by="anteil", ascending=False).head(20)
    prozent_df = (top20[relevante_klassen].T / top20["gesamt"]).T * 100

    farben = {
        "sehr gering": "darkgreen",
        "gering": "green",
        "mittel": "gold",
        "hoch": "orange",
        "sehr hoch": "red",
    }
    schriftfarben = {
        "sehr gering": "white",
        "gering": "white",
        "mittel": "black",
        "hoch": "black",
        "sehr hoch": "black",
    }

    # Plot erstellen
    fig, ax = plt.subplots(figsize=(14, 8))
    prozent_df.plot(
        kind="bar",
        stacked=True,
        color=[farben[r] for r in relevante_klassen],
        ax=ax,
    )

    # Prozentwerte eintragen
    for i, (idx, row) in enumerate(prozent_df.iterrows()):
        y_offset = 0
        for risiko in relevante_klassen:
            wert = row[risiko]
            if pd.notna(wert) and wert > 3:
                ax.text(
                    i, y_offset + wert / 2,
                    f"{wert:.0f}%",
                    ha="center", va="center",
                    color=schriftfarben[risiko],
                    fontsize=8,
                    fontweight="bold"
                )
            y_offset += wert

    ax.set_title(titel, fontsize=14)
    ax.set_xlabel("Gemeinde")
    ax.set_ylabel("Anteil in %")
    ax.set_ylim(0, 100)
    ax.legend(title="Hochwasserrisiko", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right")
    plt.tight_layout()
    plt.show()   

# === 3. Skript ausführen ===
if __name__ == "__main__":
    gdf = lade_gebaeude_mit_risiko(shapefile_path, raster_path)

    # Diagramm-Variante 1: Top 20 hohes Risiko
    erstelle_plot(gdf, modus="hoch")

    # Diagramm-Variante 2: Top 20 niedriges Risiko
    #erstelle_plot(gdf, modus="niedrig")
