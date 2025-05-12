import sqlite3
import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

# Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")

def fetch_vocab_from_db(limit=5):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang
        FROM vocabulary
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def generate_example_sentence(word, lang_code="de"):
    prompt = f"Schreibe einen kurzen, einfachen Satz auf {lang_code}, in dem das Wort '{word}' sinnvoll vorkommt."
    response = model.generate_content(prompt)
    return response.text.strip()

def check_if_translation_used(user_sentence, expected_word):
    return expected_word.lower() in user_sentence.lower()

def evaluate_translation_with_gemini(source_sentence, user_translation, expected_word, target_lang):
    prompt = f"""Bewerte die folgende Benutzerübersetzung:

🟦 Ursprungssatz ({target_lang}): "{source_sentence}"
🟨 Benutzerübersetzung: "{user_translation}"
🟩 Erwartetes Wort: "{expected_word}"

1. Wird das erwartete Wort sinnvoll verwendet?
2. Ist die Übersetzung insgesamt grammatikalisch und sinngemäß korrekt?
3. Verbesserungsvorschläge?

Antworte in 3 kurzen Punkten auf Deutsch.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def start_vocab_quiz():
    print("📘 Vokabeltest startet!\n")
    vocab_list = fetch_vocab_from_db()
    results = []

    for idx, (v_id, original, translation, source_lang, target_lang) in enumerate(vocab_list, 1):
        print(f"{idx}. Übersetze: '{original}' ({source_lang} ➜ {target_lang})")
        user_input = input("   ➤ Deine Übersetzung: ").strip().lower()
        correct = user_input == translation.lower()

        if correct:
            print("✅ Richtig!")
        else:
            print(f"❌ Falsch. Richtig wäre: {translation}")

        # Beispielsatz generieren
        lang_code = source_lang.split("-")[0]
        try:
            example = generate_example_sentence(original, lang_code)
            print(f"\n📖 Beispielsatz in {lang_code}: {example}")
        except Exception as e:
            print(f"⚠️ Fehler bei Satzgenerierung: {e}")
            continue

        # Benutzer soll Satz übersetzen
        user_translation = input("🔄 Übersetze den Satz ins Zielsprachlich: ").strip()

        # Check: Wort enthalten?
        word_used = check_if_translation_used(user_translation, translation)
        if word_used:
            print("✅ Das übersetzte Wort wurde korrekt verwendet!")
        else:
            print(f"⚠️ Das Wort '{translation}' scheint in deiner Übersetzung zu fehlen.")

        # Gemini-Bewertung
        try:
            feedback = evaluate_translation_with_gemini(example, user_translation, translation, target_lang)
            print(f"\n🔍 Gemini-Feedback:\n{feedback}")
        except Exception as e:
            feedback = f"⚠️ Bewertung nicht möglich: {e}"
            print(feedback)

        # Ergebnis speichern
        results.append({
            "original": original,
            "translation": translation,
            "user_input": user_input,
            "correct": correct,
            "example_sentence": example,
            "user_translation": user_translation,
            "word_used": word_used,
            "feedback": feedback
        })

        print("-" * 60)

    # Zusammenfassung
    correct_count = sum(1 for r in results if r["correct"] and r["word_used"])
    total = len(results)
    percentage = round(100 * correct_count / total, 1)

    print("\n📊 Test-Zusammenfassung")
    print(f"✅ Richtig beantwortet (Wort + Satz): {correct_count} von {total} ({percentage}%)\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. Wort: {r['original']} ➜ {r['translation']}")
        print(f"   ➤ Deine Eingabe: {r['user_input']}")
        print(f"   ➤ Satz-Übersetzung korrekt: {'✅' if r['word_used'] else '❌'}")
        print(f"   🧠 Feedback-Auszug: {r['feedback'].splitlines()[0]}")
        print()

if __name__ == "__main__":
    start_vocab_quiz()
