
#Erstellt ein gestapeltes Histogramm der Gebäude nach Haushaltsgröße und Hochwasserrisiko in Prozent
#auf Basis der geclippten Gebäudedaten in Unterfranken.

#Input:
#- data/shapefiles/buildings_unterfranken_clipped.shp
#- data/raster/HSM_WoE_C.tif 

#Output:
#- Anzeige des Histogramms im Plot-Fenster 


import geopandas as gpd
import rasterio
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint

# === 1. Histogrammerstellung ===

def create_histogram(buildings_path="data/shapefiles/buildings_unterfranken_clipped.shp",
                     raster_path="data/raster/HSM_WoE_C.tif"):

    # 1. Gebäudepunkte laden
    gdf = gpd.read_file(buildings_path)

    # 2. MultiPoints aufspalten 
    def explode_multipoints(gdf):
        rows = []
        for idx, row in gdf.iterrows():
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

    # 3. Raster laden & Risiko-Werte extrahieren
    with rasterio.open(raster_path) as src:
        coords = [(geom.x, geom.y) for geom in gdf.geometry]
        risiko_values = [val[0] if val else None for val in src.sample(coords)]
    gdf["Risiko"] = risiko_values

    # 4. Nur gültige Daten verwenden
    gdf = gdf.dropna(subset=["Risiko", "geb_bewohn"])
    gdf = gdf[gdf["geb_bewohn"] > 0]

    # 5. Risiko-Klassen definieren
    bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
    gdf["Risiko_Klasse"] = pd.cut(
        gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True
    )

    # 6. Haushaltsgrößenklassen definieren 
    bins_bewohner = [0, 2, 5, 10, 20, 50, 100, float("inf")]
    labels_bewohner = ["1–2", "3–5", "6–10", "11–20", "21–50", "51–100", "100+"]
    gdf["Bewohner_Klasse"] = pd.cut(
        gdf["geb_bewohn"], bins=bins_bewohner, labels=labels_bewohner, include_lowest=True
    )

    # 7. Gruppieren & Prozentualisieren
    grouped = gdf.groupby(["Bewohner_Klasse", "Risiko_Klasse"], observed=False).size().unstack(fill_value=0)
    grouped_pct = grouped.div(grouped.sum(axis=1), axis=0) * 100

    # 8. Farben definieren
    farben = {
        "sehr gering": "darkgreen",
        "gering": "green",
        "mittel": "gold",
        "hoch": "orange",
        "sehr hoch": "red"
    }

    # 9. Plot erstellen
    fig, ax = plt.subplots(figsize=(12, 7))
    grouped_pct.plot(
        kind="bar",
        stacked=True,
        color=[farben[label] for label in grouped_pct.columns],
        ax=ax
    )

    # 10. Prozentwerte in Balken eintragen
    for i, haushalt in enumerate(grouped_pct.index):
        bottom = 0
        for risiko in grouped_pct.columns:
            value = grouped_pct.loc[haushalt, risiko]
            if value > 3:
                text_color = "black" if risiko in ["mittel", "hoch", "sehr hoch"] else "white"
                ax.text(
                    i,
                    bottom + value / 2,
                    f"{value:.0f}%",
                    ha='center',
                    va='center',
                    color=text_color,
                    fontsize=9,
                    fontweight='bold'
                )
            bottom += value

    # 11. Layout & Beschriftung
    ax.set_ylabel("Anteil der Gebäude (%)")
    ax.set_xlabel("Haushaltsgröße (Bewohner pro Gebäude)")
    ax.set_title("Anteil Gebäude pro Hochwasserrisikoklasse je Haushaltstyp (in %)")
    ax.legend(title="Hochwasserrisiko", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()



# === 2. Skript ausführen ===
if __name__ == "__main__":
    create_histogram()
