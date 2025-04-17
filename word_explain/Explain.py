import google.generativeai as genai
from configuration.config import GEMINI_API_KEY  # 🔑 Hole Key aus config.py

# Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)

# Funktion zum Erklären eines markierten Wortes im Kontext
def explain_word(translated_text, selected_word):
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    
    prompt = (
    f"Erkläre das Wort „{selected_word}“, wie es im folgenden Satz verwendet wird: „{translated_text}“.\n"
    f"Erstelle eine verständliche, gut strukturierte Erklärung für Sprachlerner und beantworte die folgenden Punkte in ganzen Sätzen:\n\n"

    f"**1. Bedeutung:**\n"
    f"Was bedeutet das Wort in diesem konkreten Satz? Erkläre es in einem vollständigen Satz mit Beispielen.\n\n"

    f"**2. Herkunft:**\n"
    f"Woher stammt das Wort historisch? Gib die sprachliche Herkunft und eventuelle ursprüngliche Bedeutung an.\n\n"

    f"**3. Grammatikalische Rolle:**\n"
    f"Welche Wortart hat das Wort in diesem Satz (z. B. Adjektiv, Substantiv, Verb) und wie wird es dort verwendet?\n\n"

    f"**4. Beispiel in anderem Kontext:**\n"
    f"Gib einen weiteren Beispielsatz, in dem das Wort verwendet wird – aber in einem anderen Zusammenhang.\n\n"

    f"Antworte ausschließlich mit dem formatierten Erklärungstext – ohne Einleitung, ohne Begrüßung."
)



    gemini_response = model.generate_content(prompt)
    return gemini_response.text.strip()
