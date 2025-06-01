import whisper
import os
import torch
import gc  # für Speicherfreigabe

# Whisper-Cache-Verzeichnis setzen (falls nicht vorhanden)
cache_dir = "C:/Users/flori/openai_whisper_chache/"
os.makedirs(cache_dir, exist_ok=True)
os.environ["XDG_CACHE_HOME"] = cache_dir

# Modellwahl
model_name = "base"  # Alternativen: "tiny", "small", "medium", "large"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model(model_name, device=device)

def transcribe_audio(audio_path):
    try:
        print(f"📁 Starte Transkription auf Gerät: {device.upper()} ...")
        
        result = model.transcribe(audio_path, fp16=(device == "cuda"))
        
        text = result.get("text", "").strip()
        print("✅ Transkription erfolgreich.")
        return text

    except Exception as e:
        return f"❌ Fehler bei Transkription: {str(e)}"
    
    finally:
        # 🔁 Speicher aufräumen (optional, vor allem bei vielen Durchläufen)
        gc.collect()

