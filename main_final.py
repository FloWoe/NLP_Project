from Translation.translator import translate_text
from word_explain.Explain import explain_word
from word_finding.word_alignment import find_matching_word_crosslingual

def main():
    # === Benutzerinput ===
    text = input("Gib den zu übersetzenden Text ein: ")
    target_lang = input("Zielsprache (z. B. en, ja, de, fr): ")

    try:
        # === Übersetzen ===
        translated = translate_text(text, target_lang)
        print("\n🔁 Übersetzung:", translated)

        # === Markiertes Wort auswählen (aus der Übersetzung) ===
        selected_word = input("🔎 Welches Wort möchtest du erklärt bekommen (aus der Übersetzung)? ")

        # === Worterklärung durch Gemini ===
        explanation = explain_word(translated, selected_word)
        print("\n📘 Worterklärung:")
        print(explanation)

        # === Zugehöriges Wort im Originaltext finden ===
        zugeordnetes_wort = find_matching_word_crosslingual(
            sentence_lang1=text,
            sentence_lang2=translated,
            selected_word=selected_word,
            selected_language_code="lang2"  # Das markierte Wort stammt aus der Übersetzung
        )

        print(f"\n🔗 Zugehöriges Wort im Originaltext: {zugeordnetes_wort}")

    except Exception as e:
        print("❌ Fehler:")
        print(e)

if __name__ == "__main__":
    main()
