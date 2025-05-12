from Translation.translator import translate_text
from word_explain.Explain import explain_word
from word_finding.word_alignment import find_matching_word_crosslingual
from speech_module.tts_Google import synthesize_speech
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
        difficulty = difficulty_map.get(level, "medium")
        text = generate_text_by_language(lang, difficulty)
        print(f"📄 Generierter Lerntext ({difficulty}):\n{text}")
    else:
        # Standardtesttext
        text = input("\nGib deinen eigenen Text ein oder drücke Enter für einen Testtext:\n") or \
            "Ich spiele jeden Sonntag mit meinen Freunden Fußball. Letztes Wochenende haben wir wieder gespielt."

    # Ziel- und Ausgangssprache
    target_ui_lang = input("Zielsprache (z. B. en-US, de-DE): ").strip() or "en-US"
    source_ui_lang = "de-DE" if "de" in text.lower() else "en-US"

    # ISO-Codes: "de", "en"
    source_lang = "de" if "de" in source_ui_lang.lower() else "en"
    target_lang = "de" if "de" in target_ui_lang.lower() else "en"

    try:
        # === Übersetzen ===
        translated = translate_text(text, target_lang)
        print("\n🔁 Übersetzung:", translated)

        # === TTS abspielen ===
        tts_lang_code = target_ui_lang
        output_path = synthesize_speech(translated, output_path="Test_tts.mp3", lang=tts_lang_code)
        if output_path:
            print("🔊 Audio erzeugt:", output_path)

        # === Markiertes Wort auswählen ===
        selected_word = input("🔎 Welches Wort möchtest du erklärt bekommen (aus der Übersetzung)? ").strip()

        # === Worterklärung durch Gemini ===
        explanation = explain_word(translated, selected_word)
        print("\n📘 Worterklärung:")
        print(explanation)

        # === Sprachrichtung und passende Sätze festlegen ===
        # Wenn selected_word aus Übersetzung, ist das source_lang = target_lang
        sentence_lang1 = translated
        sentence_lang2 = text

        result = find_matching_word_crosslingual(
            sentence_lang1=sentence_lang1,
            sentence_lang2=sentence_lang2,
            selected_word=selected_word,
            source_lang=target_lang,
            target_lang=source_lang
        )

        print("\n✅ Wortvergleich abgeschlossen")
        print(f"- Markiertes Wort:        {result['selected_word']}  → Lemma: {result['selected_lemma']}")
        print(f"- Gefundenes Wort:        {result['matched_word']}  → Lemma: {result['matched_lemma']}")
        print(f"- Übereinstimmung:        {'JA ✅' if result['match_success'] else 'NEIN ❌'}")
        print("🟦 Original Matches:", result["original_matches"])
        print("🟩 Translated Matches:", result["translated_matches"])

    except Exception as e:
        print("❌ Fehler:")
        print(e)


if __name__ == "__main__":
    main()
