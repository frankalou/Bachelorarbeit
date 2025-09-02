
# Erstellt ein gestapeltes Balkendiagramm nach Hochwasserrisiko
# für Flächen der Städte Aschaffenburg, Würzburg und Schweinfurt.
#
# Input:
# - data/shapefiles/flaechen_gemeinden_risiko_fuzzy90.shp
#
# Output:
# - Anzeige des Diagramms im Plot-Fenster

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# === Diagramm erstellen ===

# 1. Daten laden
shp_path = "data/shapefiles/flaechen_gemeinden_risiko_unterfranken.shp"
gdf = gpd.read_file(shp_path)

# 2. Städte auswählen
auswahl_staedte = ["Aschaffenburg", "Würzburg", "Schweinfurt"]
gdf_auswahl = gdf[gdf["GEN"].isin(auswahl_staedte)].copy()

# 3. Prozentspalten und Farben definieren
labels_pct = ["s_ger_pct", "ger_pct", "mit_pct", "hoch_pct", "s_hoch_pct"]
risiko_klassen = labels_pct.copy()

farben = {
    "s_ger_pct": "darkgreen",
    "ger_pct": "green",
    "mit_pct": "gold",
    "hoch_pct": "orange",
    "s_hoch_pct": "red"
}
schriftfarben = {
    "s_ger_pct": "white",
    "ger_pct": "white",
    "mit_pct": "black",
    "hoch_pct": "black",
    "s_hoch_pct": "black"
}

# DataFrame für Plot vorbereiten
prozent_df = gdf_auswahl.set_index("GEN")[labels_pct]
prozent_df = prozent_df.loc[auswahl_staedte]  

# 4. Balkendiagramm erstellen
fig, ax = plt.subplots(figsize=(10, 6))

bars = prozent_df.plot(
    kind="bar",
    stacked=True,
    color=[farben[r] for r in risiko_klassen],
    ax=ax,
    legend=False,
    width=0.5  
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

# Achsen und Layout
ax.set_title("Hochwasserrisikoanteil der Flächen in Aschaffenburg, Würzburg und Schweinfurt", fontsize=14, pad=15)
ax.set_xlabel("")
ax.set_ylabel("Anteil in %")
ax.set_ylim(0, 100)
ax.set_xticklabels(auswahl_staedte, rotation=0, fontsize=12)
ax.grid(axis="y", linestyle="--", alpha=0.5)

# Legende hinzufügen
legenden_namen = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
handles, _ = ax.get_legend_handles_labels()
ax.legend(handles, legenden_namen, title="Hochwasserrisiko", bbox_to_anchor=(1.05, 1), loc="upper left")

plt.tight_layout()
plt.show()
