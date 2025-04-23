# NLP Project
# 📚 Vokabeltrainer mit Textmarkierung

## Beschreibung des Projektes


## 📝 Projektidee

Unsere Anwendung soll beim Vokabellernen unterstützen. Nutzer*innen können z. B. Songtexte oder andere Texte in ein Eingabefeld einfügen. Der Text wird auf Wunsch automatisch übersetzt.

Ein zentrales Feature ist die Möglichkeit, Wörter im Originaltext farblich zu markieren – diese Markierungen werden automatisch auch in der Übersetzung übernommen. Dadurch können gezielt neue Vokabeln im Kontext gelernt werden. Des weiteren soll bei den Markierungen Wörter erklärt werdne hinsichtlich der Herkunft, Bedeutung im Satz, Wortart und in einem anderen Kontext überführt werden als Beispiel. Dadurch soll dem Lernen ermöglicht werden effizient neue Wörter zu lernen und sie einprägsamer zu machen, da andere Kontextbeispiele für das Wort aufgezeigt werden.

<div style="display: flex; justify-content: center; gap: 20px;">
  <img src="images/Idee.png" alt="Screenshot 1" width="400"/>
  <img src="images/explain.jpg" alt="Screenshot 2" width="400"/>
</div>

<p style="text-align: center;"><em>Abb.1: Beispielhafte Umsetzung unseres Vokabeltrainers.</em></p>




💡 Die Anwendung hat einen hohen Praxisbezug, erfordert allerdings einiges an Frontend-Arbeit.

---

## 👥 Gruppenmitglieder

- Maxi Zvada  
- Lukas Ihrig  
- Florian Wölfel  
- Noah Schlotz  
- Marius Essig


## 🚀 Installation & Setup

### 1. 📦 Voraussetzungen

- Python 3.10 oder höher
- [Node.js](https://nodejs.org/) (nur für Dev-Tools, optional)
- Paketmanager wie `pip`

### 2. 🔁 Repository klonen

```bash
git clone https://github.com/dein-nutzername/dein-repo.git
cd dein-repo
```

### 3.📥 ffmpeg installieren (erforderlich für Audioaufnahme)

#### 🪟 Windows:

1. Lade `ffmpeg` von: [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Entpacke z. B. nach:  
   `C:\ffmpeg`
3. Füge `C:\ffmpeg\bin` zu deiner **System-Umgebungsvariable `PATH`** hinzu.
4. Starte dein Terminal neu und überprüfe mit:

```bash
ffmpeg -version
```

### 4. API Key erstellen

ggf. muss auch neue KPI Keys für die Speech-to-Text, Text-to-Speech, Gemini und der Google Cloud Translation API neue API Keys erstellt werden.

### 5. Anwendung starten
```bash
python app.py
```
#### 🌐 Anwendung im Browser öffnen

Öffne deinen Browser und gehe zu:
[Zum Übersetzer](http://127.0.0.1:5000)



