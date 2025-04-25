from generate_text.gap_generator import create_gap_text_with_gemini

if __name__ == "__main__":
    beispiel_satz = "Die Katze schläft auf dem Sofa."
    result = create_gap_text_with_gemini(beispiel_satz)

    print("📝 Ursprünglicher Satz:", beispiel_satz)
    print("🔎 Lückentext:", result.get("gap_text"))
    print("✅ Gesuchtes Wort:", result.get("original_word"))
    print("🛠️  Raw:", result.get("raw", "OK"))
