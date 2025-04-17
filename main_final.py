from Translation.translator import translate_text
from word_explain.Explain import explain_word

def main():
    # === Benutzerinput ===
    text = input("Gib den zu übersetzenden Text ein: ")
    target_lang = input("Zielsprache (z. B. en, ja, de, fr): ")

    try:
        # === Übersetzen ===
        translated = translate_text(text, target_lang)
        print("\n🔁 Übersetzung:", translated)

        # === Wort erklären lassen ===
        selected_word = input("🔎 Welches Wort möchtest du erklärt bekommen (aus der Übersetzung)? ")
        explanation = explain_word(translated, selected_word)

        print("\n📘 Worterklärung:")
        print(explanation)

    except Exception as e:
        print("❌ Fehler:")
        print(e)


if __name__ == "__main__":
    main()
