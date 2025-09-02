
#Erstellt ein gestapeltes Balkendiagramm der Hochwasserrisikoanteile
#nach Gemeindefläche in Unterfranken.

#Input:
#- data/shapefiles/flaechen_gemeinden_risiko_unterfranken.shp

#Output:
#- Anzeige des Histogramms im Plot-Fenster

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# === Histogrammerstellung ===

# 1. Shapefile laden
shp_path = "data/shapefiles/flaechen_gemeinden_risiko_unterfranken.shp"
gdf = gpd.read_file(shp_path)

# 2. Prozent-Spalten und Farben definieren
labels_pct = ["s_ger_pct", "ger_pct", "mit_pct", "hoch_pct", "s_hoch_pct"]
farben = {
    "s_ger": "darkgreen",
    "ger": "green",
    "mit": "gold",
    "hoch": "orange",
    "s_hoch": "red"
}

# 3. NaN durch 0 ersetzen 
gdf[labels_pct] = gdf[labels_pct].fillna(0)
gdf["sum_risiko"] = gdf[labels_pct].sum(axis=1)
gdf_nonzero = gdf[gdf["sum_risiko"] > 0].copy()

# 4. Sortieren nach dem Risiko "sehr hoch" 
gdf_sorted = gdf_nonzero.sort_values(by="s_hoch_pct", ascending=False).reset_index(drop=True)

# 5. Diagramm erstellen
x = np.arange(len(gdf_sorted))
bottom = np.zeros(len(gdf_sorted))
segment_oberkanten = []  # Für Trennlinien

fig, ax = plt.subplots(figsize=(18, 8))

for label in labels_pct:
    key = label.replace("_pct", "")
    values = gdf_sorted[label].values
    ax.bar(x, values, bottom=bottom, color=farben[key], edgecolor='none', width=1.0)
    segment_oberkanten.append(bottom + values)
    bottom += values

# Trennlinien zwischen den Risikoklassen
for y_vals in segment_oberkanten[:-1]:
    ax.plot(x, y_vals, color="black", linestyle="--", linewidth=0.8, alpha=0.7)

# Marker-Städte
marker_staedte = ["Würzburg", "Schweinfurt", "Aschaffenburg"]
for stadt in marker_staedte:
    try:
        idx = gdf_sorted[gdf_sorted["GEN"] == stadt].index[0]
        ax.axvline(x=idx, color="black", linestyle="--", linewidth=1)
        ax.text(
            idx, 100, stadt,
            rotation=90, va="top", ha="center", fontsize=9, fontweight="bold", color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=2),
            transform=ax.transData
        )
    except IndexError:
        print(f"{stadt} nicht gefunden!")

# Horizontale Hilfslinien
for y in range(20, 101, 20):
    ax.axhline(y=y, color="gray", linestyle="dashed", linewidth=0.5, alpha=0.7)
    ax.text(-1, y, f"{y}%", va="center", ha="right", fontsize=8, color="gray")

# Achsen & Layout
ax.set_xlim(-0.5, len(x) - 0.5)
ax.set_ylim(0, 100)

# x-Ticks, alle 50 Gemeinden
tick_step = 50
ax.set_xticks(np.arange(0, len(x), tick_step))

ax.set_xlabel("Gemeinden (sortiert nach Anteil sehr hohes Risiko)")
ax.set_ylabel("Hochwasserrisikoanteil in %")
ax.set_title("Hochwasserrisikoanteil nach Gemeindeflächen in Unterfranken")

# 9. Legende erstellen
legenden_labels = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
legenden_farben = ["darkgreen", "green", "gold", "orange", "red"]
legenden_patches = [Patch(color=f, label=l) for f, l in zip(legenden_farben, legenden_labels)]
ax.legend(handles=legenden_patches, title="Risikoklassen", loc="upper left", bbox_to_anchor=(1, 1))

plt.tight_layout()
plt.show()
