import os
import pyperclip

# Pfad zum Ordner mit den .html-Dateien (aktuell das Arbeitsverzeichnis)
ordner_pfad = "."

# Liste für Inhalte
alle_inhalte = []

# Alle .html-Dateien im Ordner durchgehen
for dateiname in os.listdir(ordner_pfad):
    if dateiname.endswith(".html"):
        pfad = os.path.join(ordner_pfad, dateiname)
        with open(pfad, "r", encoding="utf-8") as f:
            inhalt = f.read()
            eintrag = f"=== {dateiname} ===\n{inhalt}\n"
            alle_inhalte.append(eintrag)

# Alles zusammenfügen
gesamttext = "\n\n".join(alle_inhalte)

# In die Zwischenablage kopieren
pyperclip.copy(gesamttext)

print("Alle HTML-Inhalte wurden in die Zwischenablage kopiert.")
