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
        return response.json()["data"]["translations"][0]["translatedText"]
    else:
        raise Exception("Fehler bei der Übersetzung")
