import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import os

# === 1. CSV-Eingabe & Ausgabe-Datei ===
csv_datei = os.path.join("..", "data", "csv", "Zensus2022.csv")
output_tables_folder = os.path.join("..", "outputs", "tables")
os.makedirs(output_tables_folder, exist_ok=True)
output_datei = os.path.join(output_tables_folder, "unterfranken_polygon.csv")
chunk_size = 100_000  # Zeilen pro Chunk

# === 2. Funktion: DMS → Dezimalgrad ===
def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

# === 3. Ursprüngliche Koordinaten in DMS (Unterfranken grob abgesteckt) ===
koordinaten_dms = [
    ((49, 32, 30.54, 'N'), (8, 51, 10.63, 'E')),   # Punkt 1
    ((49, 24, 38.26, 'N'), (10, 44, 28.60, 'E')),  # Punkt 2
    ((50, 28, 27.07, 'N'), (10, 58, 50.11, 'E')),  # Punkt 3
    ((50, 42, 6.96,  'N'), (9, 5, 21.97,  'E'))    # Punkt 4
]

# === 4. DMS → Dezimalgrad ===
punkte_dd = [(dms_to_dd(*lat), dms_to_dd(*lon)) for lat, lon in koordinaten_dms]

# === 5. Umwandlung EPSG:4326 → EPSG:3035 ===
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
punkte_3035 = [transformer.transform(lon, lat) for lat, lon in punkte_dd]

# === 6. Polygon aus Koordinaten erzeugen ===
polygon = Polygon(punkte_3035)

# === 7. Spaltennamen ===
x_spalte = "x_mp_100m"
y_spalte = "y_mp_100m"

# === 8. Alte Output-Datei löschen, falls vorhanden ===
if os.path.exists(output_datei):
    os.remove(output_datei)

# === 9. Verarbeitung starten ===
print("Beginne Verarbeitung in Chunks...")

for i, chunk in enumerate(pd.read_csv(csv_datei, sep=';', chunksize=chunk_size)):
    print(f"Verarbeite Chunk {i + 1}...")

    # Spaltenprüfung
    if x_spalte not in chunk.columns or y_spalte not in chunk.columns:
        raise ValueError("Die CSV enthält nicht die erwarteten Spalten!")

    # Punkt-Geometrie erstellen
    geometry = [Point(xy) for xy in zip(chunk[x_spalte], chunk[y_spalte])]
    gdf = gpd.GeoDataFrame(chunk, geometry=geometry, crs="EPSG:3035")

    # Filtern innerhalb des Polygons
    gdf_filtered = gdf[gdf.within(polygon)]

    # Falls Treffer vorhanden → speichern
    if not gdf_filtered.empty:
        gdf_filtered.drop(columns="geometry").to_csv(
            output_datei, sep=';', mode='a',
            header=not os.path.exists(output_datei),
            index=False
        )
        print(f"{len(gdf_filtered)} Zeilen gespeichert.")
    else:
        print("Keine passenden Zeilen in diesem Chunk.")

print(f"Fertig! Gefilterte Daten gespeichert in: {os.path.abspath(output_datei)}")
