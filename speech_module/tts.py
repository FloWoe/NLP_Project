import requests
from configuration.config import GOOGLE_TTS_API_KEY

def synthesize_speech(text, output_path="output.mp3", lang="de-DE"):
    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}"

        # Anfrage-Payload
        payload = {
            "input": {
                "text": text
            },
            "voice": {
                "languageCode": lang,
                "name": "de-DE-Wavenet-B",
                "ssmlGender": "NEUTRAL"
            },
            "audioConfig": {
                "audioEncoding": "MP3"
            }
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
