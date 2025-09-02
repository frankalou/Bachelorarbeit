
# Erstellt ein gestapeltes Balkendiagramm der Gebäude nach Hochwasserrisiko
# für die Städte Aschaffenburg, Würzburg und Schweinfurt.
# 
# Input:
# - data/shapefiles/buildings_unterfranken.shp
# - data/raster/HSM_WoE_C.tif
#
# Output:
# - Anzeige des Diagramms im Plot-Fenster

import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# === Diagramm erstellen ===

# 1. Shapefile laden und Raster extrahieren
gdf = gpd.read_file("data/shapefiles/buildings_unterfranken.shp")
raster_path = "data/raster/HSM_WoE_C.tif"

with rasterio.open(raster_path) as src:
    # reprojizieren, falls nötig
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

    coords = [(geom.x, geom.y) for geom in gdf.geometry]
    risiko_values = [val[0] if val[0] != src.nodata else np.nan for val in src.sample(coords)]

# Risiko-Werte zum GeoDataFrame hinzufügen
gdf["Risiko"] = risiko_values

# 2. Risikoklassen zuordnen
bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

gdf = gdf.dropna(subset=["Risiko"]) 
gdf["Risiko_Klasse"] = pd.cut(gdf["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

# 3. Farben definieren
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
risiko_klassen = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]

# 4. Städte auswählen
auswahl_staedte = ["Aschaffenburg", "Würzburg", "Schweinfurt"]
gdf_auswahl = gdf[gdf['LocalityNa'].isin(auswahl_staedte)]

# 5. Gruppieren & Prozentwerte berechnen
gruppen = gdf_auswahl.groupby(["LocalityNa", "Risiko_Klasse"]).size().unstack(fill_value=0)
gruppen = gruppen[risiko_klassen]  

prozent_df = (gruppen.T / gruppen.sum(axis=1)).T * 100
prozent_df = prozent_df.loc[auswahl_staedte] 

# 6. Balkendiagramm erstellen
fig, ax = plt.subplots(figsize=(10, 6))

bars = prozent_df.plot(
    kind="bar",
    stacked=True,
    color=[farben[r] for r in risiko_klassen],
    ax=ax,
    legend=False
)

# Prozentwerte in Balken eintragen
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
                fontsize=10,
                fontweight="bold"
            )
        y_offset += wert

# Achsen & Layout
ax.set_title(
    "Hochwasserrisikoanteil der Gebäude in Aschaffenburg, Würzburg und Schweinfurt",
    fontsize=14, pad=15
)
ax.set_ylabel("Anteil in %")
ax.set_xlabel("")
ax.set_ylim(0, 100)
ax.set_xticklabels(auswahl_staedte, rotation=0, fontsize=12)
ax.grid(axis="y", linestyle="--", alpha=0.5)

# Legend hinzufügen
ax.legend(risiko_klassen, title="Hochwasserrisiko", bbox_to_anchor=(1.05, 1), loc="upper left")

plt.tight_layout()
plt.show()
