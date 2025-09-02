
#Erstellt zwei Histogramme zur Verteilung der Gesamtbevölkerung und der über 65-Jährigen
#nach Hochwasserrisiko in Unterfranken.

#Input:
#- data/excel/unterfranken_ueber65_absolut.xlsx
#- data/raster/HSM_WoE_C.tif 

#Output:
#- Anzeige von zwei Histogrammen:
#  1. absolute Anzahl (Gesamtbevölkerung und über 65-Jährige)
#  2. Prozentuale Verteilung

import pandas as pd
import numpy as np
import rasterio
from pyproj import CRS, Transformer
import matplotlib.pyplot as plt

# === 1. Histogramme erstellen ===

def create_histograms(excel_path="data/excel/unterfranken_ueber65_absolut.xlsx",
                      raster_path="data/raster/HSM_WoE_C.tif"):
    # 1. Excel laden
    df_all = pd.read_excel(excel_path)

    # 2. Raster laden
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs

    # 3. CRS definieren
    crs_excel = CRS.from_epsg(3035)  
    crs_raster = raster_crs          

    # 4. Transformer erstellen
    transformer = Transformer.from_crs(crs_excel, crs_raster, always_xy=True)

    # 5. Koordinaten transformieren 
    x_coords = df_all["x_mp_100m_x"].values
    y_coords = df_all["y_mp_100m_x"].values
    x_raster, y_raster = transformer.transform(x_coords, y_coords)
    coords = list(zip(x_raster, y_raster))

    # 6. Rasterwerte auslesen
    with rasterio.open(raster_path) as src:
        nodata = src.nodata
        risiko_values = []
        for val in src.sample(coords):
            risiko = val[0]
            if nodata is not None and risiko == nodata:
                risiko_values.append(np.nan)
            else:
                risiko_values.append(risiko)

    df_all["Risiko"] = risiko_values

    # 7. Gültige Zeilen filtern
    df_all = df_all.dropna(subset=["Risiko", "Einwohner", "Ueber65_Absolut"])
    df_all = df_all[(df_all["Einwohner"] > 0) & (df_all["Ueber65_Absolut"] > 0)]

    # 8. Risiko-Klassen definieren
    bins_risiko = [-18.459, -10.999, -6.982, -2.62, 2.546, 10.81]
    labels_risiko = ["sehr gering", "gering", "mittel", "hoch", "sehr hoch"]
    df_all["Risiko_Klasse"] = pd.cut(df_all["Risiko"], bins=bins_risiko, labels=labels_risiko, include_lowest=True)

    # 9. Absolute Verteilung (Gesamt und Ü65)
    gesamt = df_all.groupby("Risiko_Klasse")["Einwohner"].sum().reindex(labels_risiko)
    ueber65 = df_all.groupby("Risiko_Klasse")["Ueber65_Absolut"].sum().reindex(labels_risiko)

    x = np.arange(len(labels_risiko))
    breite = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - breite/2, gesamt, breite, label='Gesamtbevölkerung', color='lightblue')
    ax.bar(x + breite/2, ueber65, breite, label='Über 65-Jährige', color='salmon')

    ax.set_xlabel("Hochwasserrisiko")
    ax.set_ylabel("Anzahl Personen")
    ax.set_title("Verteilung der Gesamtbevölkerung und der über 65-jährigen nach Hochwasserrisiko")
    ax.set_xticks(x)
    ax.set_xticklabels(labels_risiko)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()

    # 10. Prozentuale Verteilung
    gesamt_prozent = (gesamt / gesamt.sum()) * 100
    ueber65_prozent = (ueber65 / ueber65.sum()) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - breite/2, gesamt_prozent, breite, label='Gesamtbevölkerung', color='lightblue')
    ax.bar(x + breite/2, ueber65_prozent, breite, label='Über 65-Jährige', color='salmon')

    ax.set_xlabel("Hochwasserrisiko")
    ax.set_ylabel("Anteil in %")
    ax.set_title("Prozentuale Verteilung der Gesamtbevölkerung und der über 65-jährigen nach Hochwasserrisiko")
    ax.set_xticks(x)
    ax.set_xticklabels(labels_risiko)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # 11. Prozentwerte über Balken anzeigen
    for i, (g, u) in enumerate(zip(gesamt_prozent, ueber65_prozent)):
        ax.text(i - breite/2, g + 0.3, f"{g:.1f}%", ha='center', fontsize=9)
        ax.text(i + breite/2, u + 0.3, f"{u:.1f}%", ha='center', fontsize=9)

    plt.tight_layout()
    plt.show()

# === 2. Skript ausführen ===
if __name__ == "__main__":
    create_histograms()
