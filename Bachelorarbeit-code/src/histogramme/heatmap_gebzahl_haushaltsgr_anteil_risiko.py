
#Heatmap: Prozentualer Anteil der Gebäude nach Hochwasserrisiko und Haushaltsgröße.

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp
#- data/raster/HSM_WoE_C.tif

#Output:
#- Heatmap-Plot im Plot-Fenster


import geopandas as gpd
import rasterio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point, MultiPoint

# === 1.MultiPoints aufspalten ===

def explode_multipoints(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Zerlegt MultiPoint-Geometrien in einzelne Points."""
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

def main():
    # 1. Daten laden
    shp_path = "data/shapefiles/buildings_unterfranken_clipped.shp"
    raster_path = "data/raster/HSM_WoE_C.tif"

    gdf = gpd.read_file(shp_path)
    gdf = explode_multipoints(gdf)

    # 2. Hochwasserrisiko aus Raster extrahieren
    with rasterio.open(raster_path) as src:
        coords = [(geom.x, geom.y) for geom in gdf.geometry]
        risiko_values = [val[0] if val else None for val in src.sample(coords)]

    gdf["Risiko"] = risiko_values

    # 3. Daten bereinigen
    gdf = gdf.dropna(subset=["Risiko", "geb_bewohn"])
    gdf = gdf[gdf["geb_bewohn"] > 0]
    gdf = gdf[gdf["geb_bewohn"] <= 200]

    # 4. Klassen einteilen
    bins_risiko = [-18.459, -11, -7, -2.6, 2.5, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
    gdf["Risiko_Klasse"] = pd.cut(
        gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True
    )

    bins_bewohner = [0, 2, 5, 10, 20, 50, 100, float("inf")]
    labels_bewohner = ["1–2", "3–5", "6–10", "11–20", "21–50", "51–100", "100+"]
    gdf["Bewohner_Klasse"] = pd.cut(
        gdf["geb_bewohn"], bins=bins_bewohner, labels=labels_bewohner, include_lowest=True
    )

    # 5. Gruppieren und Prozentwerte berechnen
    heatmap_data = gdf.groupby(["Bewohner_Klasse", "Risiko_Klasse"], observed=False).size().unstack(fill_value=0)
    heatmap_percent = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100

    # Y-Achse
    heatmap_percent = heatmap_percent.reindex(index=labels_bewohner[::-1])

    # 6. Heatmap erstellen
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        heatmap_percent,
        annot=True,
        fmt=".1f",
        cmap="rocket_r",  
        linewidths=0.5,
        linecolor="gray",
        cbar_kws={"label": "Anteil in %"},
    )
    plt.xlabel("Hochwasserrisiko")
    plt.ylabel("Bewohner pro Gebäude (Klassen)")
    plt.title("Prozentualer Anteil der Gebäude pro Risiko- und Haushaltsklasse")
    plt.tight_layout()
    plt.show()

# === 3. Skript-Einstiegspunkt ===

if __name__ == "__main__":
    main()
