import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def explain_word(translated_text, selected_word):
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    prompt = (
        f"Erkläre das Wort „{selected_word}“, wie es im folgenden Satz verwendet wird: „{translated_text}“.\n"
        f"Erstelle eine verständliche, strukturierte Erklärung für Sprachlerner mit folgenden Abschnitten:\n\n"
        f"1. Bedeutung\n"
        f"2. Herkunft\n"
        f"3. Grammatikalische Rolle\n"
        f"4. Beispiel in anderem Kontext\n\n"
        f"Formatiere deine Antwort ausschließlich mit HTML:\n"
        f"- Verwende <p> für jeden Absatz\n"
        f"- Verwende <strong> für jede Abschnittsüberschrift\n"
        f"- Gib KEINEN Markdown-Code zurück (kein ```html, keine Sterne ** etc.)\n"
        f"- Gib KEINEN Codeblock zurück\n"
        f"- Gib NUR HTML aus, keine Kommentare, keine Einleitungen\n"
    )

    gemini_response = model.generate_content(prompt)
    html_output = gemini_response.text.strip()

    # Sicherheits-Backup: Entferne eventuelle Markdown-Reste
    if html_output.startswith("```html") or html_output.startswith("```"):
        html_output = html_output.replace("```html", "").replace("```", "").strip()

    return html_output
