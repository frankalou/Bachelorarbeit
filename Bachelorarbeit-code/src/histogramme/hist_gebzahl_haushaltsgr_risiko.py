
#Erstellt ein Histogramm der Gebäudeanzahl nach Haushaltsgröße und Hochwasserrisiko,
#inklusive Zoomfenster für größere Haushalte.

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp
#- data/raster/HSM_WoE_C.tif 

#Output:
#- Anzeige des Histogramms im Plot-Fenster

import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point, MultiPoint

# === 1.MultiPoints aufspalten ===

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

def create_histogram():
    # 1. Gebäudepunkte laden 
    buildings_path = "data/shapefiles/buildings_unterfranken_clipped.shp"
    gdf = gpd.read_file(buildings_path)
    gdf = explode_multipoints(gdf)

    # 2. Raster laden
    raster_path = "data/raster/HSM_WoE_C.tif"
    with rasterio.open(raster_path) as src:
        coords = [(geom.x, geom.y) for geom in gdf.geometry]
        risiko_values = [val[0] if val else None for val in src.sample(coords)]

    # 3. Risiko-Werte hinzufügen
    gdf["Risiko"] = risiko_values
    gdf = gdf.dropna(subset=["Risiko", "geb_bewohn"])
    gdf = gdf[gdf["geb_bewohn"] > 0]

    # 4. Klassen definieren
    bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
    gdf["Risiko_Klasse"] = pd.cut(gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

    bins_bewohner = [0, 2, 5, 10, 20, 50, 100, float("inf")]
    labels_bewohner = ["1–2", "3–5", "6–10", "11–20", "21–50", "51–100", "100+"]
    gdf["Bewohner_Klasse"] = pd.cut(gdf["geb_bewohn"], bins=bins_bewohner, labels=labels_bewohner, include_lowest=True)

    farben = {
        "sehr gering": "darkgreen",
        "gering": "green",
        "mittel": "gold",
        "hoch": "orange",
        "sehr hoch": "red"
    }

    # 5. Gruppierung
    grouped = gdf.groupby(["Bewohner_Klasse", "Risiko_Klasse"], observed=False).size().unstack(fill_value=0)

    # 6. Hauptplot
    fig, ax = plt.subplots(figsize=(14, 7))
    grouped.plot(kind="bar", stacked=True, color=[farben[label] for label in labels_risiko], ax=ax)
    ax.set_xlabel("Bewohner pro Gebäude")
    ax.set_ylabel("Anzahl Gebäude")
    ax.set_title("Gebäudeanzahl pro Haushaltsgröße und Hochwasserrisiko")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(title="Hochwasserrisiko", loc='center left', bbox_to_anchor=(1.01, 0.5))

    # Zoomfenster 1 (11–50 Personen)
    grouped_zoom1 = grouped.loc[["11–20", "21–50"]]
    axins1 = fig.add_axes([0.53, 0.58, 0.15, 0.3])
    grouped_zoom1.plot(kind="bar", stacked=True, color=[farben[l] for l in labels_risiko], ax=axins1, legend=False)
    axins1.set_title("Zoom: 11–50 Personen", fontsize=10)
    axins1.set_ylim(0, 10000)
    axins1.tick_params(labelsize=8)
    axins1.grid(axis="y", linestyle="--", alpha=0.4)

    # Zoomfenster 2 (51+ Personen)
    grouped_zoom2 = grouped.loc[["51–100", "100+"]]
    axins2 = fig.add_axes([0.71, 0.58, 0.15, 0.3])
    grouped_zoom2.plot(kind="bar", stacked=True, color=[farben[l] for l in labels_risiko], ax=axins2, legend=False)
    axins2.set_title("Zoom: 51+ Personen", fontsize=10)
    axins2.set_ylim(0, 400)
    axins2.tick_params(labelsize=8)
    axins2.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.show()

# === 3.Skript ausführen ===

if __name__ == "__main__":
    create_histogram()
