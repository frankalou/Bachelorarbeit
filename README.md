# Bachelorarbeit - Räumliche Analyse der Hochwassergefährdung in Unterfranken: Bewertung der Risiken für Bevölkerung und Gebäude

Dieses Repository enthält die Python Skripte und die Projektstruktur meiner Bachelorarbeit.

Hinweis: Die Input-Daten (`data/`) sind aus Datenschutzgründen nicht im Repository enthalten und werden separat bereitgestellt.

Projektstruktur:  
data/ (nicht im Repository enthalten)  
├── gml/  
├── csv/  
│ └── unterfranken_polygon.csv  
├── excel/  
│ ├── unterfranken_ueber65_absolut.xlsx  
│ └── Alter_in_10er-Jahresgruppen_Unterfranken_polygon.xlsx  
├── shapefiles/  
│ ├── VG5000_GEM.shp  
│ ├── Unterfranken.shp  
│ ├── buildings_unterfranken.shp  
│ ├── buildings_unterfranken_clipped.shp  
│ ├── flaechen_gemeinden_risiko_unterfranken.shp  
│ └── top20_gemeinden_unterfranken_risiko.shp  
└── raster/  
└── HSM_WoE_C.tif  

scripts/  
├── histogramme/  
│ ├── heatmap_gebzahl_haushaltsgr_anteil_risiko.py  
│ ├── heatmap_gebzahl_haushaltsgrStadt_anteil_risiko.py  
│ ├── hist_altersgruppe_risiko.py  
│ ├── hist_bevgesamt_ue65_risiko.py  
│ ├── hist_flaeche_gemeinde_risiko.py  
│ ├── hist_flaecheStadt_anteil_risiko.py  
│ ├── hist_gebzahl_gemeinde_risiko.py  
│ ├── hist_gebzahl_haushaltsgr_anteil_risiko.py  
│ ├── hist_gebzahl_haushaltsgr_risiko.py  
│ ├── hist_gebzahlStadt_anteil_risiko.py  
│ ├── hist_top20_gebzahl_risiko.py  
│ └── hist_top20_gemeinde_risiko.py  
├── weitere_scripts/  
│ ├── Anzahl_ueber_65.py  
│ ├── Gemeindeflaechen_Hochwasserrisiko.py  
│ ├── Top20_Gemeinden_Risiko.py 
│ └── Vergleich_Gebaeudefunktion.py  
├── main_gebaeudedaten.py  
└── main_unterfranken_filter.py  

outputs/  
├── tables/  
└── shapefiles/  

requirements.txt  
README.md  
