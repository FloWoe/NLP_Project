import requests
from configuration.config import GOOGLE_TTS_API_KEY

# Mapping von Sprache zu passender Stimme
# Einfaches Mapping für häufige Sprachen
VOICE_MAPPING = {
    "de-DE": "de-DE-Chirp-HD-D",
    "en-US": "en-US-Wavenet-A",
    "fr-FR": "fr-FR-Wavenet-A",
    "es-ES": "es-ES-Chirp-HD-D",
    "ja-JP": "ja-JP-Wavenet-A"
}


def synthesize_speech(text, output_path="output.mp3", lang="de-DE"):
    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}"

        # Sprachcode und Stimme extrahieren
        lang_code = lang.split("-")[0]  # z. B. "de" aus "de-DE"
        voice_name = VOICE_MAPPING.get(lang, "en-US-Wavenet-D")  # Fallback
        payload = {
            "input": { "text": text },
            "voice": {
            "languageCode": lang,
            "name": voice_name,
            "ssmlGender": "NEUTRAL"},
            "audioConfig": { "audioEncoding": "MP3" }
}


        response = requests.post(url, json=payload)
        response.raise_for_status()
        audio_content = response.json()["audioContent"]

        # Base64-decoding und speichern
        import base64
        with open(output_path, "wb") as out:
            out.write(base64.b64decode(audio_content))
            print(f"🔊 Gespeichert als: {output_path}")

        return output_path

    except Exception as e:
        print("❌ Fehler bei der Sprachausgabe:", e)
        return None

