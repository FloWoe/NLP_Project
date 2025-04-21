import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

# Konfiguriere Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def find_matching_word_crosslingual(sentence_lang1, sentence_lang2, selected_word, selected_language_code):
    """
    Findet das entsprechende Wort in der jeweils anderen Sprache mithilfe von Gemini.

    :param sentence_lang1: Originalsatz in Sprache 1
    :param sentence_lang2: Übersetzter Satz in Sprache 2
    :param selected_word: Vom Nutzer markiertes Wort
    :param selected_language_code: Sprachcode des markierten Wortes (z. B. 'en', 'de', 'fr')
    :return: Passendes Wort im anderen Satz
    """
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    lang_1_label = "Satz 1"
    lang_2_label = "Satz 2"

    prompt = (
        f"In einem Sprachvergleich wurde in folgendem Satz das Wort „{selected_word}“ markiert:\n\n"
        f"{lang_1_label if selected_language_code == 'lang1' else lang_2_label}: \"{sentence_lang1 if selected_language_code == 'lang1' else sentence_lang2}\"\n\n"
        f"Der zugehörige Satz in der anderen Sprache lautet:\n"
        f"{lang_2_label if selected_language_code == 'lang1' else lang_1_label}: \"{sentence_lang2 if selected_language_code == 'lang1' else sentence_lang1}\"\n\n"
        f"Welches Wort in dem anderen Satz entspricht dem markierten Wort?\n\n"
        f"Gib **nur das zugehörige Wort** aus – keine Erklärung, keine Einleitung, keine Sätze."
    )

    try:
        gemini_response = model.generate_content(prompt)
        return gemini_response.text.strip()
    except Exception as e:
        return f"(Fehler bei Gemini: {e})"
