import google.generativeai as genai
import json
import re
from configuration.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def create_gap_text_with_gemini(text: str) -> dict:
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    prompt = (
    f"Ich gebe dir einen ganzen Text. Wähle EIN sinnvolles Wort aus und ersetze es im gesamten Originaltext durch eine Lücke (_____). Es soll nur eine Lücke im gesamten Text geben."
    f"Gib den KOMPLETTEN Text mit der Lücke zurück, nicht nur einen Satzteil. "
    f"Gib das Ergebnis als JSON im Format zurück:\n"
    f'{{"gap_text": "...", "original_word": "..."}}\n\n'
    f"Text: {text}"
)


    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    try:
        # Entferne Markdown-Codeblöcke falls vorhanden (```json ... ```)
        json_match = re.search(r'{.*}', raw_text, re.DOTALL)
        if not json_match:
            raise ValueError("Kein gültiger JSON-Block gefunden")

        json_data = json.loads(json_match.group(0))
        return json_data

    except Exception as e:
        return {
            "gap_text": text,
            "original_word": None,
            "error": str(e),
            "raw": raw_text
        }
