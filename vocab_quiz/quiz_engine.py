# quiz_engine.py

import sqlite3
import google.generativeai as genai
from configuration.config import GEMINI_API_KEY # Stelle sicher, dass dieser Import funktioniert
import os

# BASE_DIR und DB_PATH werden hier definiert, aber es wäre sauberer,
# wenn DB-Operationen ausschließlich über Funktionen aus vocab_db.py liefen.
# Für jetzt behalten wir es bei, um die Änderungen minimal zu halten,
# aber langfristig ist eine Kapselung der DB-Logik in vocab_db.py besser.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'Database', 'vocab.db')


# 🔹 Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash") # oder dein spezifisches Modell


# 🔹 Vokabeln abrufen – JETZT mit user_id und optionalem Sprachfilter
def fetch_vocab_from_db(user_id: int, limit: int = 5, lang_code: str = None): # NEU: user_id Parameter
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT id, original_word, translated_word, source_lang, target_lang
        FROM vocabulary
        WHERE user_id = ?  -- NEU: Filter nach user_id
    """
    params = [user_id]

    if lang_code:
        query += " AND target_lang LIKE ?"
        params.append(f"{lang_code}%")

    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows


# 🔹 Beispiel-Satz generieren (in Sprache der Originalvokabel)
# Diese Funktion bleibt unverändert, da sie nicht direkt von user_id abhängt.
def generate_example_sentence(word: str, lang_code: str = "de") -> str:
    prompt = f"Schreibe einen kurzen, sinnvollen Beispielsatz auf {lang_code}, in dem das Wort '{word}' vorkommt."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Fehler bei Satzgenerierung für '{word}' ({lang_code}): {e}")
        return f"(Fehler bei Satzgenerierung für {word})"


# 🔹 Einfacher Wortabgleich
# Bleibt unverändert.
def check_if_translation_used(user_sentence: str, expected_word: str) -> bool:
    return expected_word.lower() in user_sentence.lower()


# 🔹 Übersetzung mit Gemini bewerten
# Bleibt unverändert, da die Bewertungslogik an sich nicht user-spezifisch ist.
def evaluate_translation_with_gemini(source_sentence: str, user_translation: str, expected_word: str, target_lang: str) -> str:
    prompt = f"""
Bewerte die folgende Benutzerübersetzung im Vergleich zum Ursprungssatz:

Ursprungssatz (Deutsch): "{source_sentence}"
Benutzerübersetzung: "{user_translation}"
Erwartetes Wort (muss nicht zwingend im Satz vorkommen, dient als Kontext): "{expected_word}"

Gib ausschließlich einen vollständigen, verbesserten Satz auf {target_lang} zurück – **ohne Einleitung, Kommentare oder Erklärungen**.
Wenn die Benutzerübersetzung bereits grammatikalisch korrekt und semantisch passend ist, gib nur exakt das Wort "OK" zurück – **ohne weitere Zusätze**.
Wenn die Benutzerübersetzung komplett falsch ist oder keinen Sinn ergibt, gib eine kurze, konstruktive Korrektur oder einen komplett neuen korrekten Satz zurück.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Fehler bei Gemini-Bewertung: {str(e)}")
        return "⚠️ Fehler bei der Bewertung durch KI."


# 🔹 Konsolenversion des Vokabeltests – JETZT mit user_id
def start_vocab_quiz(user_id: int, lang_code: str = None): # NEU: user_id Parameter
    print(f"📘 Vokabeltest für User ID {user_id} startet!\n")
    # Ruft die angepasste Funktion fetch_vocab_from_db auf
    vocab_list = fetch_vocab_from_db(user_id=user_id, lang_code=lang_code) # NEU: user_id übergeben
    
    if not vocab_list:
        print(f"Keine Vokabeln für User ID {user_id} gefunden (ggf. mit Sprachfilter '{lang_code}').")
        print("Stelle sicher, dass der User Vokabeln gespeichert hat.")
        return

    results = []

    for idx, (v_id, original, translation, source_lang, target_lang) in enumerate(vocab_list, 1):
        print(f"{idx}. Übersetze: '{original}' ({source_lang} ➜ {target_lang})")
        user_input_word = input("   ➤ Deine Übersetzung (Wort): ").strip().lower()
        word_correct = user_input_word == translation.lower()

        if word_correct:
            print("✅ Wort Richtig!")
        else:
            print(f"❌ Wort Falsch. Richtig wäre: {translation}")

        # Beispielsatz generieren (in Sprache der Quellvokabel)
        # source_lang könnte None sein, wenn Daten unvollständig sind
        lang_code_for_sentence_generation = source_lang.split("-")[0] if source_lang else "de" # Fallback
        
        example_sentence = ""
        try:
            example_sentence = generate_example_sentence(original, lang_code_for_sentence_generation)
            print(f"\n📖 Beispielsatz ({lang_code_for_sentence_generation}): {example_sentence}")
        except Exception as e:
            # Fehler wurde schon in generate_example_sentence geloggt
            print(f"Konnte keinen Beispielsatz für '{original}' generieren.")
            # Optional: Quiz für dieses Wort abbrechen oder ohne Satz weiterführen
            # continue

        user_translation_sentence = ""
        word_used_in_sentence = False
        feedback_from_gemini = "Keine Satzübersetzung angefordert/bewertet."

        if example_sentence and not example_sentence.startswith("(Fehler bei Satzgenerierung"):
            user_translation_sentence = input(f"🔄 Übersetze den Satz ins Zielsprachliche ({target_lang}): ").strip()

            if user_translation_sentence: # Nur bewerten, wenn eine Eingabe erfolgte
                word_used_in_sentence = check_if_translation_used(user_translation_sentence, translation)
                if word_used_in_sentence:
                    print("👍 Das erwartete Wort wurde in deiner Satzübersetzung verwendet.")
                else:
                    print(f"🤔 Das Wort '{translation}' fehlt wahrscheinlich in deiner Satzübersetzung.")

                # Feedback durch Gemini generieren
                try:
                    feedback_from_gemini = evaluate_translation_with_gemini(example_sentence, user_translation_sentence, translation, target_lang)
                    print(f"\n🔍 Gemini-Feedback:\n{feedback_from_gemini}")
                except Exception as e:
                    # Fehler wurde schon in evaluate_translation_with_gemini geloggt
                    feedback_from_gemini = "Bewertung durch KI nicht möglich."
                    print(feedback_from_gemini)
            else:
                print("Keine Satzübersetzung eingegeben.")
        
        results.append({
            "original": original,
            "translation": translation,
            "user_input_word": user_input_word,
            "word_correct": word_correct,
            "example_sentence": example_sentence,
            "user_translation_sentence": user_translation_sentence,
            "word_used_in_sentence": word_used_in_sentence,
            "feedback_from_gemini": feedback_from_gemini
        })

        print("-" * 60)

    # Zusammenfassung
    if not results:
        print("Keine Ergebnisse zum Zusammenfassen.")
        return

    # Zähle "richtig", wenn das Wort korrekt war UND im Satz verwendet wurde (falls ein Satz bewertet wurde)
    overall_correct_count = 0
    for r in results:
        if r["word_correct"]:
            if r["user_translation_sentence"]: # Wenn ein Satz übersetzt wurde
                if r["word_used_in_sentence"]: # und das Wort darin vorkam
                    overall_correct_count +=1
            else: # Wenn nur das Wort abgefragt wurde (kein Satz generiert/übersetzt)
                overall_correct_count +=1

    total_questions = len(results)
    percentage = round(100 * overall_correct_count / total_questions, 1) if total_questions > 0 else 0

    print("\n📊 Test-Zusammenfassung")
    print(f"Gesamtbewertung (Wort richtig & ggf. im Satz verwendet): {overall_correct_count} von {total_questions} ({percentage}%)\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. Wort: {r['original']} ({'✅' if r['word_correct'] else '❌'})")
        if r["example_sentence"] and not r["example_sentence"].startswith("(Fehler bei Satzgenerierung"):
            print(f"   Satz verwendet '{r['translation']}'? {'👍' if r['word_used_in_sentence'] else '🤔'}")
            print(f"   Dein Satz: {r['user_translation_sentence']}")
            print(f"   KI Feedback: {r['feedback_from_gemini'].splitlines()[0]}")
        print()


# Test-Einstiegspunkt
if __name__ == "__main__":
    # Für lokale Tests müsstest du hier eine existierende user_id eingeben
    # oder eine kleine Logik einbauen, um einen Testuser zu erstellen/abzufragen.
    # Beispiel:
    test_user_id = 1 # Annahme: User mit ID 1 existiert
    
    # Alternativ, Erstellung eines Testusers (erfordert create_user Funktion aus vocab_db)
    # from vocab_storage.vocab_db import create_user, get_user_by_username
    # test_username = "quiztester"
    # test_email = "quiztester@example.com"
    # test_password = "password123"
    # existing_user = get_user_by_username(test_username)
    # if existing_user:
    #     test_user_id = existing_user[0]
    # else:
    #     test_user_id = create_user(test_username, test_email, test_password)
    #     if not test_user_id:
    #         print("Konnte Testuser nicht erstellen. Breche ab.")
    #         exit()
    #     print(f"Testuser '{test_username}' mit ID {test_user_id} erstellt/verwendet.")


    lang_filter_code = input(f"🔤 Sprache für den Test für User {test_user_id} (z.B. en, fr, es, leer für alle): ").strip()
    start_vocab_quiz(user_id=test_user_id, lang_code=lang_filter_code if lang_filter_code else None)