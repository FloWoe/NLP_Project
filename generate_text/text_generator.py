import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def generate_text_by_language(language_code: str, difficulty: str = "medium") -> str:
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    difficulty_descriptions = {
        "easy": "Texte in sehr einfachen und kurzen Sätzen, ideal für Anfänger. Erstelle jedes Mal eine individuelle Kurzgeschichte, Kindergeschichte oder Alltagsszene mit klarer, leicht verständlicher Struktur.",
  
        "medium": "Texte mit mittlerem Schwierigkeitsgrad in allgemein verständlicher Sprache. Zum Beispiel ein einfacher Zeitungsartikel, ein Liedtext, ein Text aus dem Bereich Sport oder (dezent formulierter) erotischer Literatur. Der Text sollte alltagstauglich, interessant und gut lesbar sein.",
  
        "hard": "Texte mit komplexer Satzstruktur und anspruchsvollem Vokabular, z. B. aus Fachbereichen wie Wirtschaft, Technik, Biologie, Künstliche Intelligenz oder wissenschaftlichen Publikationen. Ideal sind Abschnitte aus Forschungsartikeln oder Themen mit hohem intellektuellem Anspruch."
}

    difficulty_description = difficulty_descriptions.get(difficulty, difficulty_descriptions["medium"])

    prompt = (
        f"Erstelle einen kurzen Text mit etwa 50 Wörtern in der Sprache '{language_code}'.\n"
        f"Der Text soll geeignet sein zum Vokabellernen und aus {difficulty_description} bestehen.\n"
        f"Gib nur den Text selbst aus, ohne Erklärungen oder Titel.\n"
        f"Der Text soll maximal 40-60 Wöter beinhalten, nicht mehr!\n"
        f"Keine Einleitung oder begrüßung. Gebe mir einfach nur diesen generierten text zurück.\n"
        f"Schreibe unterschiedliche Geschichten. Es sollen nicht immer der gleiche Wortlauf und Inhalt sein. Bei jedem Aufruf soll es ein Text mit komplett anderem Inhalt, also einen andern je nach dem gewählten Schwierigkeitsbereich sein. Ändere den Text bei jedem Abruf"
    )

    gemini_response = model.generate_content(prompt)
    return gemini_response.text.strip()
