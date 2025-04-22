import whisper
import os

# Optional: Setze ein alternatives Cache-Verzeichnis für Whisper (vermeidet Pfadprobleme)
os.environ["XDG_CACHE_HOME"] = "C:/Users/noahs/whisper_cache"

model = whisper.load_model("base")

def transcribe_audio(audio_path):
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        return f"❌ Fehler bei Transkription: {str(e)}"
