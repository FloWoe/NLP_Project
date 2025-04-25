import os
import uuid
from elevenlabs import ElevenLabs, save
from configuration.config import ELEVENLABS_API_KEY


# API-Key setzen
client = ElevenLabs (api_key=ELEVENLABS_API_KEY)

# Rachel Voice-ID (multilingual)
RACHEL_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

import os

def synthesize_speech(text, output_path=None, lang="de-DE"):
    try:
        # Standard-Ausgabepfad setzen, falls keiner angegeben ist
        if output_path is None:
            output_path = os.path.join("Backend", "output.mp3")
        else:
            # Falls output_path als String ("Backend\output.mp3") übergeben wird
            output_path = os.path.normpath(output_path)

        # Sicherstellen, dass der Ordner existiert
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Audio mit Rachel generieren (emotionaler eingestellt)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=RACHEL_VOICE_ID,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.2,            # niedrigere Stabilität = mehr Variation = natürlicher, emotionaler
                "similarity_boost": 0.75,     # gute Balance aus Klarheit und Natürlichkeit
                "style_exaggeration": 1.5     # stärker betonter Stil (geht je nach Modell bis etwa 2.0)
            }
        )

        # Audiodatei speichern
        save(audio, output_path)
        print(f"🔊 Audio gespeichert unter: {output_path}")

        return output_path

    except Exception as e:
        print(f"❌ Fehler bei der Sprachausgabe: {e}")
        return None
