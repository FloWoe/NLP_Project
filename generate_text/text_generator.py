import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def generate_text_by_language(language_code: str, difficulty: str = "medium") -> str:
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    difficulty_descriptions = {
        "easy": "einfachen Sätzen für Anfänger (z. B. Kindertexte, Kurzgeschichte)",
        "medium": "allgemein verständlichen Sätzen mit mittlerem Schwierigkeitsgrad (vielleicht ein songtext oder ein einfach Zeitschriftartikel über ein einfach verstädnliches Ereignis)",
        "hard": "komplexen Sätzen aus z. B. Wirtschafts- oder Fachartikeln. Wissenschafltiche texte"
    }

    difficulty_description = difficulty_descriptions.get(difficulty, difficulty_descriptions["medium"])

    prompt = (
        f"Erstelle einen kurzen Text mit etwa 50 Wörtern in der Sprache '{language_code}'.\n"
        f"Der Text soll geeignet sein zum Vokabellernen und aus {difficulty_description} bestehen.\n"
        f"Gib nur den Text selbst aus, ohne Erklärungen oder Titel.\n"
        f"Keine Einleitung oder begrüßung. Gebe mir einfach nur diesen generierten text zurück.\n"
        f"Schreibe unterschiedliche Geschichten. Es sollen nicht immer der gleiche Wortlauf und Inhalt sein. Bei jedem Aufruf soll es ein Text mit komplett anderem Inhalt sein"
    )

    gemini_response = model.generate_content(prompt)
    return gemini_response.text.strip()
