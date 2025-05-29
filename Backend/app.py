import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from Translation.translator import translate_text
from word_finding.word_alignment import find_matching_word_crosslingual
from word_explain.Explain import explain_word
from speech_module.stt_whisper import transcribe_audio
from speech_module.tts_Elevenlab import synthesize_speech
from generate_text.text_generator import generate_text_by_language
from generate_text.gap_generator import create_gap_text_with_gemini
from learning.learning_engine import  get_next_vocab,update_learning_progress,check_daily_goal_achieved,get_session_progress,reset_session,  get_next_vocab, update_learning_progress,reset_session, check_daily_goal_achieved
from vocab_storage.vocab_db import init_db, init_learning_table, init_learning_progress_table, get_random_vocab_entry, VocabEntry, save_vocab, get_all_vocab, sqlite3, get_vocab_by_target_lang, search_vocab_advanced, init_result_table, VocabEntry, get_vocab_by_target_lang,save_quiz_result, get_all_results, get_summary_stats
from vocab_quiz.quiz_engine import start_vocab_quiz, evaluate_translation_with_gemini
import google.generativeai as genai
from learning.learning_engine import (
    get_next_vocab,
    update_learning_progress,
    check_daily_goal_achieved,
    get_session_progress,
    start_new_session,
    reset_session
)

  # ✅ Aktiviert CORS für alle Routen
init_db()
init_result_table()  # Quiz-Ergebnisse-Tabelle anlegen
init_learning_table()
init_learning_progress_table()

template_path = os.path.join(os.path.dirname(__file__), "..", "templates")
static_path = os.path.join(os.path.dirname(__file__), "..", "static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "Database", "vocab.db")


app = Flask(__name__, template_folder=template_path, static_folder=static_path)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

# Weitere Seiten (optional)
@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/dashboard")
def dashboard():
    return render_template("Dashboard.html")

@app.route("/favorite")
def favorite():
    return render_template("favorite.html")

@app.route("/lernen")
def lernen():
    return render_template("lernen.html")

@app.route("/hilfe")
def hilfe():
    return render_template("hilfe.html")



@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target_lang", "en")

    try:
        result = translate_text(text, target_lang)

        # Nur Rōmaji zurückgeben, falls Japanisch
        if isinstance(result, dict):
            return jsonify(result)
        else:
            return jsonify({"translated": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/match-word", methods=["POST"])
def match_word():
    data = request.json
    sentence1 = data.get("sentence1")
    sentence2 = data.get("sentence2")
    selected_word = data.get("selectedWord")
    selected_from = data.get("selectedFrom")
    source_ui_lang = data.get("sourceLangCode", "de-DE")
    target_ui_lang = data.get("targetLangCode", "en-US")

    source_lang = source_ui_lang.split("-")[0].lower()
    target_lang = target_ui_lang.split("-")[0].lower()

    if selected_from == "lang1":
        lang1 = sentence1
        lang2 = sentence2
    else:
        lang1 = sentence2
        lang2 = sentence1
        source_lang, target_lang = target_lang, source_lang

    try:
        result = find_matching_word_crosslingual(
            sentence_lang1=lang1,
            sentence_lang2=lang2,
            selected_word=selected_word,
            source_lang=source_lang,
            target_lang=target_lang
        )

        if not isinstance(result, dict):
            return jsonify({"error": f"Ungültiges Ergebnis: {result}"}), 500
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        print("\n✅ Wortvergleich abgeschlossen")
        print(f"- Markiertes Wort:        {result['selected_word']}  → Lemma: {result['selected_lemma']}")
        print(f"- Gefundenes Wort(e):     {result['matched_word']}")  # evtl. Liste
        print(f"- Übereinstimmung:        {'JA ✅' if result['match_success'] else 'NEIN ❌'}")
        print("🗾 Original Matches:", result['original_matches'])
        print("🗱 Translated Matches:", result['translated_matches'])

        # 🔁 Absichern der Formate
        translated_matches = result.get("translated_matches", [])
        if not translated_matches:
            matched_raw = result.get("matched_word", "")
            if isinstance(matched_raw, str):
                translated_matches = [matched_raw]
            elif isinstance(matched_raw, list):
                translated_matches = matched_raw

        return jsonify({
            "selectedWord": result["selected_word"],
            "selectedLemma": result["selected_lemma"],
            "matchedWord": (
                result["matched_word"]
                if isinstance(result["matched_word"], str)
                else ", ".join(result["matched_word"])
            ),
            "matchedLemma": result["matched_lemma"]
                if isinstance(result["matched_lemma"], str)
                else ", ".join(result["matched_lemma"]),
            "originalMatches": result["original_matches"],
            "translatedMatches": translated_matches,
            "matchSuccess": result["match_success"]
        })

    except Exception as e:
        print("❌ Fehler in /match-word:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/explain-word", methods=["POST"])
def explain():
    data = request.get_json()
    sentence = data.get("sentence")
    word = data.get("word")

    try:
        explanation = explain_word(sentence, word)
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"explanation": f"Fehler: {str(e)}"}), 500

@app.route("/transcribe-audio", methods=["POST"])
def transcribe_audio_route():
    if "audio" not in request.files:
        return jsonify({"error": "Keine Audiodatei erhalten"}), 400

    audio_file = request.files["audio"]

    # Speichere temporär als WebM oder MP3 – abhängig vom Browser
    ext = os.path.splitext(audio_file.filename)[-1].lower()
    temp_path = os.path.join("speech_module", f"temp_input{ext}")
    audio_file.save(temp_path)

    try:
        transcription = transcribe_audio(temp_path)
        return jsonify({"transcription": transcription})
    except Exception as e:
        return jsonify({"error": f"Fehler bei Transkription: {str(e)}"}), 500
    
@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text")

        if not text:
            return {"error": "Kein Text angegeben"}, 400

        # Sprachsynthese durchführen
        output_path = synthesize_speech(text)

        # Absoluten Pfad ermitteln (damit Flask die Datei garantiert findet)
        absolute_path = os.path.abspath(output_path)

        if os.path.exists(absolute_path):
            return send_file(absolute_path, mimetype="audio/mpeg", as_attachment=False)
        else:
            return {"error": "Datei wurde nicht gefunden"}, 500

    except Exception as e:
        print("❌ Fehler im TTS-Endpoint:", e)
        return {"error": str(e)}, 500

@app.route("/generate-text", methods=["POST"])
def generate_text_route():
    data = request.get_json()
    language_code = data.get("language")  # z. B. "de", "en"
    difficulty = data.get("difficulty", "medium")  # Standard: medium

    try:
        generated_text = generate_text_by_language(language_code, difficulty)
        return jsonify({"text": generated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/gap-fill", methods=["POST"])
def gap_fill():
    data = request.get_json()
    sentence = data.get("sentence", "")

    result = create_gap_text_with_gemini(sentence)

    return jsonify(result)

@app.route("/save-vocab", methods=["POST"])
def save_vocab_route():
    data = request.get_json()
    try:
        entry = VocabEntry(
            original_word=data["original_word"],
            translated_word=data["translated_word"],
            source_lang=data["source_lang"],
            target_lang=data["target_lang"],
            original_sentence=data["original_sentence"],
            translated_sentence=data["translated_sentence"]
        )
        save_vocab(entry)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# 🔹 Route: Alle Vokabeln abrufen (inkl. ID!)
@app.route("/get-vocab", methods=["GET"])
def get_vocab():
    rows = get_all_vocab()
    result = [
        {
            "id": row[0],  # ✅ wichtig für Löschen im Frontend!
            "original_word": row[1],
            "translated_word": row[2],
            "source_lang": row[3],
            "target_lang": row[4],
            "original_sentence": row[5],
            "translated_sentence": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]
    return jsonify(result)

# 🔹 Route: Einzelne Vokabel löschen
@app.route("/delete-vocab/<int:vocab_id>", methods=["DELETE"])
def delete_vocab(vocab_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete-all-vocab", methods=["DELETE"])
def delete_all_vocab():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vocabulary")
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get-vocab-by-lang")
def get_vocab_by_lang():
    lang = request.args.get("lang", "")
    from vocab_storage.vocab_db import get_vocab_by_target_lang
    results = get_vocab_by_target_lang(lang)
    return jsonify([
        {
            "id": row[0],
            "original_word": row[1],
            "translated_word": row[2],
            "source_lang": row[3],
            "target_lang": row[4],
            "original_sentence": row[5],
            "translated_sentence": row[6],
            "created_at": row[7]
        }
        for row in results
    ])
    

@app.route("/search-vocab", methods=["GET"])
def search_vocab():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    results = search_vocab_advanced(query)  # NEU: statt fuzzy

    # Struktur bleibt gleich
    formatted = []
    for row in results:
        formatted.append({
            "id": row["id"],
            "original_word": row["original_word"],
            "translated_word": row["translated_word"],
            "source_lang": row.get("source_lang", ""),  # Optional absichern
            "target_lang": row.get("target_lang", ""),
            "original_sentence": row["original_sentence"],
            "translated_sentence": row["translated_sentence"],
            "created_at": row.get("created_at", "")
        })

    return jsonify(formatted)

@app.route("/suggest-vocab", methods=["GET"])
def suggest_vocab():
    query = request.args.get("q", "").lower()
    if not query or len(query) < 2:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT original_word FROM vocabulary
        UNION
        SELECT DISTINCT translated_word FROM vocabulary
        UNION
        SELECT DISTINCT original_sentence FROM vocabulary
        UNION
        SELECT DISTINCT translated_sentence FROM vocabulary
    """)
    all_texts = cursor.fetchall()
    conn.close()

    words = set()
    for row in all_texts:
        for word in row[0].split():
            if word.lower().startswith(query):
                words.add(word)

    return jsonify(sorted(words)[:10])  # Nur Top 10 Vorschläge


@app.route("/quiz")
def run_quiz():
    start_vocab_quiz()
    return "✅ Vokabelquiz wurde im Terminal gestartet!"

    
@app.route("/quiz-data")
def quiz_data():
    from vocab_quiz.quiz_engine import fetch_vocab_from_db, generate_example_sentence

    lang = request.args.get("lang")  # <-- Hole ausgewählte Sprache
    vocab_list = fetch_vocab_from_db(lang_code=lang)  # Übergib an die Datenbankfunktion

    results = []
    for row in vocab_list:
        v_id, original, translated, source_lang, target_lang = row
        lang_code = source_lang.split("-")[0]
        sentence = generate_example_sentence(original, lang_code)
        results.append({
            "original_word": original,
            "translated_word": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "example_sentence": sentence
        })
    return jsonify(results)



@app.route("/evaluate-answer", methods=["POST"])
def evaluate_answer():
    try:
        data = request.get_json()
        result = evaluate_translation_with_gemini(
            data["source_sentence"],
            data["user_translation"],
            data["expected_word"],
            data["target_lang"]
        )
        if not result:
            return jsonify({"feedback": "⚠️ Fehler bei der Bewertung"}), 200
        return jsonify({"feedback": result}), 200
    except Exception as e:
        print("❌ Bewertungsfehler:", str(e))
        return jsonify({"feedback": "⚠️ Fehler bei der Bewertung"}), 500




@app.route("/vocab-language-stats")
def vocab_language_stats():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_lang, COUNT(*) 
        FROM vocabulary 
        GROUP BY target_lang
    """)
    data = cursor.fetchall()
    conn.close()

    return jsonify({
        "labels": [row[0] for row in data],
        "counts": [row[1] for row in data]
    })

@app.route("/save-result", methods=["POST"])
def save_result():
    data = request.get_json()
    try:
        save_quiz_result(
            language=data.get("language", "unbekannt"),
            vocab_score=int(data.get("vocab_score", 0)),
            sentence_score=int(data.get("sentence_score", 0)),
            total_score=int(data.get("total_score", 0)),
            passed=bool(data.get("passed", False))
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/quiz-result-summary")
def quiz_result_summary():
    from vocab_storage.vocab_db import get_summary_stats
    stats = get_summary_stats()
    failed_tests = stats["total_tests"] - stats["passed_tests"]
    return jsonify({
        "passed": stats["passed_tests"],
        "failed": failed_tests
    })

@app.route("/dashboard-kpis")
def dashboard_kpis():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM quiz_results")
    total_tests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_vocab = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(total_score) FROM quiz_results")
    avg_score = cursor.fetchone()[0] or 0

    cursor.execute("SELECT total_score FROM quiz_results ORDER BY id DESC LIMIT 1")
    last_score_row = cursor.fetchone()
    last_score = last_score_row[0] if last_score_row else 0

    conn.close()

    return jsonify({
        "total_tests": total_tests,
        "total_vocab": total_vocab,
        "avg_score": round(avg_score),
        "last_score": round(last_score)
    })


@app.route("/get-learn-vocab", methods=["GET"])
def get_learn_vocab():
    vocab = get_next_vocab()
    if vocab is None:
        return jsonify({"done": True, "message": "🎉 Du hast alle Vokabeln dieser Session gelernt!"})
    return jsonify(vocab)

@app.route("/submit-vocab-result", methods=["POST"])
def submit_vocab_result():
    data = request.get_json()
    vocab_id = data.get("id")
    result = data.get("result")

    if not vocab_id or not result:
        return jsonify({"status": "error", "message": "Ungültige Daten"}), 400

    try:
        update_learning_progress(vocab_id, result)
        achieved = check_daily_goal_achieved()
        return jsonify({"status": "success", "goal_achieved": achieved})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/reset-learn-session", methods=["POST"])
def reset_learn_session():
    reset_session()
    return jsonify({"status": "reset"})

@app.route("/start-session", methods=["POST"])
def start_session():
    try:
        start_new_session()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/learning-progress", methods=["GET"])
def learning_progress():
    return jsonify(get_session_progress())









if __name__ == "__main__":
    app.run(debug=True)