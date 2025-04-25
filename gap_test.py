from generate_text.gap_generator import create_gap_text_with_gemini

if __name__ == "__main__":
    sentence = "Die Katze schläft auf dem Sofa."
    result = create_gap_text_with_gemini(sentence)

    print(f"📝 Ursprünglicher Satz: {sentence}")
    print(f"🔎 Lückentext: {result.get('gap_text')}")
    print(f"✅ Gesuchtes Wort: {result.get('original_word')}")
    print("🛠️  Raw:", result)
