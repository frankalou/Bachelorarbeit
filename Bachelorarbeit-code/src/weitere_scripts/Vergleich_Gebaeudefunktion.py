import geopandas as gpd
import pandas as pd
import os

# === INPUT SETUP ===
# Festlegen welche Shapefile ausgewertet wird
# Massbach: "Differenz_9998_1000_Massbach.shp"
# Wue: "Differenz_9998_1000_Wue.shp"
input_shapefile = "data/shapefiles/Differenz_9998_1000_Massbach.shp"

# Ausgabeordner für Ergebnisse
output_folder = "outputs/tables"
os.makedirs(output_folder, exist_ok=True)

# Name der Excel-Ausgabe (kann beliebig angepasst werden)
output_excel = os.path.join(output_folder, "Vergleich_Massbach.xlsx")

# === 1. Daten einlesen ===
gdf = gpd.read_file(input_shapefile)

# === 2. Berechnungen ===
# Anzahl der Gebäude mit Werten in den beiden Spalten
gebaeude_A = gdf["geb_bewohn"].notna().sum()
gebaeude_B = gdf["geb_bewo_1"].notna().sum()

# Durchschnittliche Bewohner pro Gebäude
avg_A = gdf["geb_bewohn"].sum() / gebaeude_A
avg_B = gdf["geb_bewo_1"].sum() / gebaeude_B

# Vergleichstabelle erstellen
vergleich = pd.DataFrame({
    "Gebäude": [gebaeude_A, gebaeude_B],
    "Ø Bewohner/Gebäude": [avg_A, avg_B]
}, index=["Shapefile A (nur Wohn)", "Shapefile B (Wohn+gemischt)"])

# Differenzen und prozentuale Veränderung berechnen
diff = vergleich.iloc[1] - vergleich.iloc[0]
perc = (diff / vergleich.iloc[0]) * 100

vergleich.loc["Differenz"] = diff
vergleich.loc["% Veränderung"] = perc

# === 3. Ergebnis ausgeben und speichern ===
print("\n=== Vergleich ===")
print(vergleich.round(2))

vergleich.to_excel(output_excel, sheet_name="Vergleich")
print(f"Excel gespeichert unter: {output_excel}")
