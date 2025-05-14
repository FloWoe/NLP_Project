import sqlite3
import google.generativeai as genai
from configuration.config import GEMINI_API_KEY

# 🔹 Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")


# 🔹 Vokabeln abrufen – mit optionalem Sprachfilter (z. B. "en")
def fetch_vocab_from_db(limit=5, lang_code=None):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()

    if lang_code:
        cursor.execute("""
            SELECT id, original_word, translated_word, source_lang, target_lang
            FROM vocabulary
            WHERE target_lang LIKE ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (f"{lang_code}%", limit))
    else:
        cursor.execute("""
            SELECT id, original_word, translated_word, source_lang, target_lang
            FROM vocabulary
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows


# 🔹 Beispiel-Satz generieren (in Sprache der Originalvokabel)
def generate_example_sentence(word, lang_code="de"):
    prompt = f"Schreibe einen kurzen, sinnvollen Beispielsatz auf {lang_code}, in dem das Wort '{word}' vorkommt."
    response = model.generate_content(prompt)
    return response.text.strip()


# 🔹 Einfacher Wortabgleich
def check_if_translation_used(user_sentence, expected_word):
    return expected_word.lower() in user_sentence.lower()


def evaluate_translation_with_gemini(source_sentence, user_translation, expected_word, target_lang):
    prompt = f"""
Beurteile die folgende Benutzerübersetzung:

🔹 Ursprungssatz: "{source_sentence}"
🔸 Benutzerübersetzung: "{user_translation}"
🔸 Erwartetes Wort: "{expected_word}"

Gib nur eine Verbesserung der Übersetzung zurück, falls nötig, als **ganzen Satz** auf {target_lang}. 
Wenn die Benutzerübersetzung korrekt ist, antworte einfach mit "OK".
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("❌ Fehler bei Gemini:", str(e))
        return "⚠️ Fehler bei der Bewertung"







# 🔹 Konsolenversion des Vokabeltests
def start_vocab_quiz(lang_code=None):
    print("📘 Vokabeltest startet!\n")
    vocab_list = fetch_vocab_from_db(lang_code=lang_code)
    results = []

    for idx, (v_id, original, translation, source_lang, target_lang) in enumerate(vocab_list, 1):
        print(f"{idx}. Übersetze: '{original}' ({source_lang} ➜ {target_lang})")
        user_input = input("   ➤ Deine Übersetzung: ").strip().lower()
        correct = user_input == translation.lower()

        if correct:
            print("✅ Richtig!")
        else:
            print(f"❌ Falsch. Richtig wäre: {translation}")

        # Beispielsatz generieren (in Sprache der Quellvokabel)
        lang_code_input = source_lang.split("-")[0]
        try:
            example = generate_example_sentence(original, lang_code_input)
            print(f"\n📖 Beispielsatz: {example}")
        except Exception as e:
            print(f"⚠️ Fehler bei Satzgenerierung: {e}")
            continue

        # Benutzerübersetzung eingeben
        user_translation = input("🔄 Übersetze den Satz ins Zielsprachlich: ").strip()

        # Check, ob Wort verwendet wurde
        word_used = check_if_translation_used(user_translation, translation)
        if word_used:
            print("✅ Das erwartete Wort wurde verwendet.")
        else:
            print(f"⚠️ Das Wort '{translation}' fehlt wahrscheinlich in deiner Übersetzung.")

        # Feedback durch Gemini generieren
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
        print(f"   ➤ Satz korrekt? {'✅' if r['word_used'] else '❌'}")
        print(f"   🧠 Feedback: {r['feedback'].splitlines()[0]}")
        print()


# Test-Einstiegspunkt
if __name__ == "__main__":
    # Optional: Sprache über Eingabe
    code = input("🔤 Sprache für den Test (z. B. en, fr, es): ").strip()
    start_vocab_quiz(lang_code=code if code else None)
