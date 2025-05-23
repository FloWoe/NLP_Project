import whisper
import os

# Whisper-Cache-Verzeichnis (optional)
os.environ["XDG_CACHE_HOME"] = "C:/Users/noahs/whisper_cache"

# Modell laden
model = whisper.load_model("medium")  # oder "large"

def transcribe_audio(audio_path):
    try:
        result = model.transcribe(audio_path, fp16=False)
        return result["text"]  # 🔹 Nur der reine Transkriptions-Text
    except Exception as e:
        return f"❌ Fehler bei Transkription: {str(e)}"

