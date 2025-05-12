import requests
from configuration.config import GOOGLE_TRANSLATE_API_KEY

def translate_text(text, target_lang):
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        'q': text,
        'target': target_lang,
        'format': 'text',
        'key': GOOGLE_TRANSLATE_API_KEY
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        translated = response.json()["data"]["translations"][0]["translatedText"]

        if target_lang == "ja":
            try:
                import pykakasi
                kakasi = pykakasi.kakasi()
                result = kakasi.convert(translated)
                reading = " ".join([item["hepburn"] for item in result])
                return {"translated": reading, "reading": reading}
            except:
                return {"translated": translated, "reading": None}
        else:
            return {"translated": translated, "reading": None}
    else:
        raise Exception("Fehler bei der Übersetzung")
