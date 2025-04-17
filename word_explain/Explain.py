import requests
import google.generativeai as genai



# === 🗝️ API-Keys ===
GOOGLE_TRANSLATE_API_KEY = "AIzaSyDY21rw19lxCvjlC-Iy8etmRmqJop_pvR8"  # Für Google Translate
GEMINI_API_KEY = "AIzaSyBZQN8kt4d7BqweJ2OLrjtNBKtG1aiy9S0"            # Für Gemini (LLM)

# === 🔧 Gemini konfigurieren ===
genai.configure(api_key=GEMINI_API_KEY)

# === 📝 Benutzereingabe ===
text = input("Gib den zu übersetzenden Text ein: ")
target_lang = input("Zielsprache (z. B. en, ja, de, fr): ")

# === 🌐 Schritt 1: Übersetzung mit Google Translate API ===
translate_url = "https://translation.googleapis.com/language/translate/v2"

params = {
    'q': text,
    'target': target_lang,
    'format': 'text',
    'key': GOOGLE_TRANSLATE_API_KEY
}

response = requests.post(translate_url, params=params)

if response.status_code == 200:
    data = response.json()
    translated = data["data"]["translations"][0]["translatedText"]
    print("\n🔁 Übersetzung:", translated)

    # === 🔍 Schritt 2: Wort auswählen & erklären lassen (Gemini Pro) ===
    selected_word = input("\n🔎 Welches Wort möchtest du erklärt bekommen? (aus der Übersetzung): ")

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    prompt = (
        f"Bitte erkläre das Wort „{selected_word}“, "
        f"wie es im folgenden Satz vorkommt: „{translated}“. "
        f"Gib auf Deutsch die Bedeutung, Herkunft (falls relevant), grammatikalische Rolle "
        f"und ein kurzes Beispiel. Zielgruppe: Sprachlerner."
        f"Antworte **ohne Begrüßung, ohne Erklärtext, ohne Einleitung**. "
    )

    gemini_response = model.generate_content(prompt)
    print("\n📘 Worterklärung:")
    print(gemini_response.text.strip())

else:
    print("❌ Fehler bei der Übersetzung:")
    print(response.text)