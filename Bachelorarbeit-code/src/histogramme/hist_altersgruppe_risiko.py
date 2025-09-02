
#Gestapeltes Balkendiagramm: Altersgruppen nach Hochwasserrisiko (prozentualer Anteil)

#Input:
#- data/excel/Alter_in_10er-Jahresgruppen_Unterfranken_polygon.xlsx
#- data/raster/HSM_WoE_C.tif

#Output:
#- Gestapeltes Balkendiagramm im Plot-Fenster

import pandas as pd
import numpy as np
import rasterio
from pyproj import Transformer
import matplotlib.pyplot as plt

# === 1. Histogramm erstellen ===

def main():
    # 1. Excel-Datei laden
    excel_path = "data/excel/Alter_in_10er-Jahresgruppen_Unterfranken_polygon.xlsx"
    df = pd.read_excel(excel_path)

    # Neue Altersgruppen-Beschriftungen
    altersgruppen_umbenannt = {
        "Unter10": "<10",
        "a10bis19": "10-19",
        "a20bis29": "20-29",
        "a30bis39": "30-39",
        "a40bis49": "40-49",
        "a50bis59": "50-59",
        "a60bis69": "60-69",
        "a70bis79": "70-79",
        "a80undaelter": ">80",
    }
    altersspaltengruppen = list(altersgruppen_umbenannt.keys())

    df = df[["x_mp_100m", "y_mp_100m", "Insgesamt_Bevoelkerung"] + altersspaltengruppen].dropna()

    # 2. Raster öffnen und Risikowerte extrahieren
    raster_path = "data/raster/HSM_WoE_C.tif"
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        nodata = src.nodata

        transformer = Transformer.from_crs("EPSG:3035", raster_crs, always_xy=True)
        x_raster, y_raster = transformer.transform(df["x_mp_100m"].values, df["y_mp_100m"].values)
        coords = list(zip(x_raster, y_raster))

        risiko_values = []
        for val in src.sample(coords):
            risiko = val[0]
            risiko_values.append(np.nan if nodata is not None and risiko == nodata else risiko)

    df["Risiko"] = risiko_values

    # 3. Risiko-Klassen zuweisen
    bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
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

    df = df.dropna(subset=["Risiko"])
    df["Risiko_Klasse"] = pd.cut(df["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

    # 4. Daten formatieren
    df_melt = df.melt(
        id_vars=["Risiko_Klasse"],
        value_vars=altersspaltengruppen,
        var_name="Altersgruppe",
        value_name="Anzahl",
    )
    df_melt["Altersgruppe"] = df_melt["Altersgruppe"].map(altersgruppen_umbenannt)
    df_melt = df_melt.dropna(subset=["Anzahl"])
    df_melt = df_melt[df_melt["Anzahl"] > 0]

    # 5. Prozentwerte berechnen
    gesamt = df_melt.groupby("Altersgruppe")["Anzahl"].sum()
    gruppen = df_melt.groupby(["Altersgruppe", "Risiko_Klasse"])["Anzahl"].sum().unstack().reindex(columns=labels_risiko)
    prozent_df = (gruppen.T / gesamt).T * 100

    # 6. Diagramm erstellen
    sortierte_altersgruppen = ["<10", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", ">80"]
    prozent_df = prozent_df.reindex(sortierte_altersgruppen)

    fig, ax = plt.subplots(figsize=(12, 6))
    prozent_df.plot(
        kind="bar",
        stacked=True,
        color=[farben[r] for r in labels_risiko],
        ax=ax,
    )

    # Prozentwerte eintragen
    for i, (_, row) in enumerate(prozent_df.iterrows()):
        y_offset = 0
        for risiko in labels_risiko:
            wert = row[risiko]
            if pd.notna(wert) and wert > 0.5:
                ax.text(
                    i, y_offset + wert / 2,
                    f"{wert:.0f}%",
                    ha="center", va="center",
                    color=schriftfarben[risiko],
                    fontsize=8,
                    fontweight="bold",
                )
                y_offset += wert

    ax.set_title("Altersgruppen nach Hochwasserrisiko (prozentual)", fontsize=14)
    ax.set_xlabel("Altersgruppe")
    ax.set_ylabel("Anteil in %")
    ax.legend(title="Hochwasserrisiko", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right")
    plt.tight_layout()
    plt.show()

# === 2. Skript ausführen ===

if __name__ == "__main__":
    main()
