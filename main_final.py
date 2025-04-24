from Translation.translator import translate_text
from word_explain.Explain import explain_word
from word_finding.word_alignment import find_matching_word_crosslingual
from speech_module.tts import synthesize_speech
from speech_module.stt_whisper import transcribe_audio
from generate_text.text_generator import generate_text_by_language

def main():
    print("\n📚 Willst du Sprache transkribieren, Text eingeben oder Lerntext automatisch generieren?")
    choice = input("Gib 'sprache', 'text' oder 'auto' ein: ").strip().lower()

    if choice == "sprache":
        audio_path = "Test_sst.mp3"
        print("🎙️ Sprache wird mit Whisper transkribiert...")
        text = transcribe_audio(audio_path)
        print(f"📝 Transkribierter Text: {text}")
    elif choice == "auto":
        lang = input("Welche Sprache soll der Lerntext haben? (z. B. en, de, fr, es, ja): ")
        print("🔢 Schwierigkeit auswählen:")
        print("  1 = Einfach\n  2 = Mittel\n  3 = Schwer")
        level = input("Wähle (1–3): ").strip()

        difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
        difficulty = difficulty_map.get(level, "medium")  # Standard: mittel

        text = generate_text_by_language(lang, difficulty)
        print(f"📄 Generierter Lerntext ({difficulty}):\n{text}")
    else:
        text = input("Gib den zu übersetzenden Text ein: ")

    target_lang = input("Zielsprache (z. B. en, ja, de, fr): ")

    try:
        # === Übersetzen ===
        translated = translate_text(text, target_lang)
        print("\n🔁 Übersetzung:", translated)

        # === TTS abspielen ===
        tts_lang_code = f"{target_lang}-DE" if target_lang != "de" else "de-DE"
        output_path = synthesize_speech(translated, output_path="Test_tts.mp3", lang=tts_lang_code)
        if output_path:
            print("🔊 Audio erzeugt:", output_path)

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
            selected_language_code="lang2"
        )

        print(f"\n🔗 Zugehöriges Wort im Originaltext: {zugeordnetes_wort}")

    except Exception as e:
        print("❌ Fehler:")
        print(e)

if __name__ == "__main__":
    main()
