import pandas as pd
import os

# === 1. Dateipfade ===
input_path = "data/excel/Unterfranken_polygon.xlsx"
output_folder = "outputs/tables"
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "unterfranken_ueber65_absolut.xlsx")

# === 2. Excel-Dateien einlesen ===
# Enthält Einwohnerzahlen pro 100m-Gitter
einwohner_df = pd.read_excel(input_path, sheet_name="Unterfranken_Einwohner")

# Enthält den Anteil der über 65-Jährigen pro 100m-Gitter
anteil_df = pd.read_excel(input_path, sheet_name="ueber65")

# === 3. Daten bereinigen ===
# Komma durch Punkt ersetzen und als float konvertieren
anteil_df["AnteilUeber65"] = (
    anteil_df["AnteilUeber65"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)
anteil_df["AnteilUeber65"] = pd.to_numeric(anteil_df["AnteilUeber65"], errors="coerce")

# === 4. Tabellen zusammenführen ===
merged = pd.merge(einwohner_df, anteil_df, on="GITTER_ID_100m")

# === 5. Absolute Anzahl über 65 Jahre berechnen ===
merged["Ueber65_Absolut"] = merged["Einwohner"] * (merged["AnteilUeber65"] / 100)

# === 6. Ergebnis ausgeben ===
print(
    merged[["GITTER_ID_100m", "Einwohner", "AnteilUeber65", "Ueber65_Absolut"]].head()
)

# === 7. Ergebnis speichern ===
merged.to_excel(output_path, index=False)
print("Datei erfolgreich gespeichert:", output_path)
