# app.py

import os
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Deine Modul-Imports
from Translation.translator import translate_text
from word_finding.word_alignment import find_matching_word_crosslingual
from word_explain.Explain import explain_word
from speech_module.stt_whisper import transcribe_audio
from speech_module.tts_Elevenlab import synthesize_speech
from generate_text.text_generator import generate_text_by_language
from generate_text.gap_generator import create_gap_text_with_gemini
from vocab_quiz.quiz_engine import start_vocab_quiz, evaluate_translation_with_gemini

# Importiere ALLE benötigten Funktionen aus vocab_db.py
from vocab_storage.vocab_db import (
    init_user_table, init_db, init_learning_table, init_learning_progress_table, init_result_table,
    VocabEntry, save_vocab, get_all_vocab, get_vocab_by_target_lang, search_vocab_advanced,
    save_quiz_result, get_all_results, get_summary_stats, get_learning_activity_over_time,
    get_language_levels, get_random_vocab_entry, # get_random_vocab_entry hinzugefügt
    create_user, get_user_by_username, get_user_by_id, get_user_by_email, # User DB Funktionen
    delete_vocab_entry, delete_all_user_vocab, # Vokabel-Löschfunktionen
    get_vocab_entry_by_id,
    sqlite3,
    get_vocab_for_quiz, # Hinzugefügt, da es in quiz_data_route verwendet wird
    check_password_hash # Hinzugefügt, da es in login Route verwendet wird
)

# Imports für learning_engine
from learning.learning_engine import (
    start_new_session as le_start_new_session, # Umbenannt, um Konflikte zu vermeiden
    get_next_vocab as le_get_next_vocab,
    update_learning_progress as le_update_learning_progress,
    check_daily_goal_achieved as le_check_daily_goal_achieved,
    get_session_progress as le_get_session_progress,
    reset_session as le_reset_session
)


# --- App Konfiguration ---
template_path = os.path.join(os.path.dirname(__file__), "..", "templates")
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "Database", "vocab.db")

app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dein-super-geheimer-schluessel-bitte-aendern!')
CORS(app)

# --- Flask-Login Konfiguration ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        # user_data ist ein Tupel: (id, username, email, password_hash)
        return User(id=user_data[0], username=user_data[1], email=user_data[2])
    return None

# --- Datenbank Initialisierung ---
init_user_table()
init_db()
init_result_table()
init_learning_table()
init_learning_progress_table()


# --- Authentifizierungs-Routen ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # flash('You are already logged in.', 'info')
        return jsonify({"status": "info", "message": "Already logged in"}), 400

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Username, email, and password are required."}), 400

        if len(password) < 6:
             return jsonify({"status": "error", "message": "Password must be at least 6 characters."}), 400

        if get_user_by_username(username):
            return jsonify({"status": "error", "message": "Username already exists. Please choose another."}), 409
        if get_user_by_email(email):
            return jsonify({"status": "error", "message": "Email address already registered. Please use another or login."}), 409

        user_id = create_user(username, email, password)
        if user_id:
            user_data = get_user_by_id(user_id)
            user_obj = User(id=user_data[0], username=user_data[1], email=user_data[2])
            login_user(user_obj)
            # flash('Registration successful! You are now logged in.', 'success')
            return jsonify({"status": "success", "message": "Registration successful. You are now logged in."})
        else:
            # flash('Registration failed. Please try again.', 'danger')
            return jsonify({"status": "error", "message": "Registration failed. Please try again."}), 500
    return jsonify({"message": "Please use POST to register."}), 405


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # flash('You are already logged in.', 'info')
        return jsonify({"status": "info", "message": "Already logged in"}), 400

    if request.method == 'POST':
        data = request.get_json()
        login_identifier = data.get('login_identifier') # Kann Username oder Email sein
        password = data.get('password')
        remember = data.get('remember', False)

        if not login_identifier or not password:
            # flash('Username/Email and password are required.', 'warning')
            return jsonify({"status": "error", "message": "Username/Email and password are required."}), 400

        user_data_by_name = get_user_by_username(login_identifier)
        user_data_by_email = get_user_by_email(login_identifier)
        
        user_data_to_check = None
        if user_data_by_name:
            user_data_to_check = user_data_by_name
        elif user_data_by_email:
            user_data_to_check = user_data_by_email

        if user_data_to_check and check_password_hash(user_data_to_check[3], password): # Index 3 ist password_hash
            user_obj = User(id=user_data_to_check[0], username=user_data_to_check[1], email=user_data_to_check[2])
            login_user(user_obj, remember=remember)
            # flash(f'Welcome back, {user_obj.username}!', 'success')
            return jsonify({"status": "success", "message": f"Login successful. Welcome, {user_obj.username}!"})
        else:
            # flash('Invalid username/email or password. Please try again.', 'danger')
            return jsonify({"status": "error", "message": "Invalid username/email or password."}), 401
    return jsonify({"message": "Please use POST to login."}), 405

@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash('You have been logged out.', 'success')
    return jsonify({"status": "success", "message": "You have been logged out."})

@app.route('/check-auth')
def check_auth_status():
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            }
        })
    return jsonify({"authenticated": False})

# --- Bestehende HTML-Seiten Routen ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/quiz")
@login_required
def quiz_page():
    return render_template("quiz.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("Dashboard.html")

@app.route("/favorite")
@login_required
def favorite():
    return render_template("favorite.html")

@app.route("/lernen")
@login_required
def lernen():
    return render_template("lernen.html")

@app.route("/hilfe")
def hilfe():
    return render_template("hilfe.html")


# --- API Endpunkte ---

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target_lang", "en")
    try:
        result = translate_text(text, target_lang)
        if isinstance(result, dict): return jsonify(result)
        else: return jsonify({"translated": result})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/match-word", methods=["POST"])
def match_word():
    data = request.json
    try:
        result = find_matching_word_crosslingual(
            sentence_lang1=data.get("sentence1") if data.get("selectedFrom") == "lang1" else data.get("sentence2"),
            sentence_lang2=data.get("sentence2") if data.get("selectedFrom") == "lang1" else data.get("sentence1"),
            selected_word=data.get("selectedWord"),
            source_lang=(data.get("sourceLangCode", "de-DE").split("-")[0].lower() if data.get("selectedFrom") == "lang1" else data.get("targetLangCode", "en-US").split("-")[0].lower()),
            target_lang=(data.get("targetLangCode", "en-US").split("-")[0].lower() if data.get("selectedFrom") == "lang1" else data.get("sourceLangCode", "de-DE").split("-")[0].lower())
        )
        if not isinstance(result, dict): return jsonify({"error": f"Ungültiges Ergebnis: {result}"}), 500
        if "error" in result: return jsonify({"error": result["error"]}), 500
        translated_matches = result.get("translated_matches", [])
        if not translated_matches:
            matched_raw = result.get("matched_word", "")
            if isinstance(matched_raw, str): translated_matches = [matched_raw]
            elif isinstance(matched_raw, list): translated_matches = matched_raw

        return jsonify({
            "selectedWord": result.get("selected_word"),
            "selectedLemma": result.get("selected_lemma"),
            "matchedWord": (result.get("matched_word") if isinstance(result.get("matched_word"), str) else ", ".join(result.get("matched_word", []))),
            "matchedLemma": (result.get("matched_lemma") if isinstance(result.get("matched_lemma"), str) else ", ".join(result.get("matched_lemma",[]))),
            "originalMatches": result.get("original_matches", []),
            "translatedMatches": translated_matches,
            "matchSuccess": result.get("match_success", False)
        })
    except Exception as e:
        print(f"❌ Fehler in /match-word: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/explain-word", methods=["POST"])
def explain():
    data = request.get_json()
    try:
        explanation = explain_word(data.get("sentence"), data.get("word"))
        return jsonify({"explanation": explanation})
    except Exception as e: return jsonify({"explanation": f"Fehler: {str(e)}"}), 500

@app.route("/transcribe-audio", methods=["POST"])
def transcribe_audio_route():
    if "audio" not in request.files: return jsonify({"error": "Keine Audiodatei erhalten"}), 400
    audio_file = request.files["audio"]
    ext = os.path.splitext(audio_file.filename)[-1].lower()
    speech_module_dir = "speech_module"
    os.makedirs(speech_module_dir, exist_ok=True)
    temp_path = os.path.join(speech_module_dir, f"temp_input{ext}")
    audio_file.save(temp_path)
    try:
        transcription = transcribe_audio(temp_path)
        return jsonify({"transcription": transcription})
    except Exception as e: return jsonify({"error": f"Fehler bei Transkription: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text")
        if not text: return {"error": "Kein Text angegeben"}, 400
        output_path = synthesize_speech(text)
        if output_path and os.path.exists(output_path):
            return send_file(os.path.abspath(output_path), mimetype="audio/mpeg", as_attachment=False)
        else: return {"error": "TTS-Datei wurde nicht gefunden oder erstellt"}, 500
    except Exception as e:
        print(f"❌ Fehler im TTS-Endpoint: {e}")
        return {"error": str(e)}, 500

@app.route("/generate-text", methods=["POST"])
def generate_text_route():
    data = request.get_json()
    try:
        generated_text = generate_text_by_language(data.get("language"), data.get("difficulty", "medium"))
        return jsonify({"text": generated_text})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/gap-fill", methods=["POST"])
def gap_fill():
    data = request.get_json()
    try:
        result = create_gap_text_with_gemini(data.get("sentence", ""))
        return jsonify(result)
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- Vokabel-spezifische Routen ---

@app.route("/save-vocab", methods=["POST"])
@login_required
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
        save_vocab(current_user.id, entry)
        return jsonify({"status": "success"})
    except KeyError as e:
        return jsonify({"status": "error", "message": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get-vocab", methods=["GET"])
@login_required
def get_vocab_route():
    rows = get_all_vocab(current_user.id)
    result = [
        {
            "id": row[0], "original_word": row[1], "translated_word": row[2],
            "source_lang": row[3], "target_lang": row[4],
            "original_sentence": row[5], "translated_sentence": row[6],
            "created_at": row[7]
        } for row in rows
    ]
    return jsonify(result)

@app.route("/delete-vocab/<int:vocab_id>", methods=["DELETE"])
@login_required
def delete_vocab_route(vocab_id):
    try:
        if delete_vocab_entry(current_user.id, vocab_id):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Vocabulary not found or not owned by user."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete-all-vocab", methods=["DELETE"])
@login_required
def delete_all_vocab_route():
    try:
        delete_all_user_vocab(current_user.id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get-vocab-by-lang")
@login_required
def get_vocab_by_lang_route():
    lang = request.args.get("lang", "")
    if not lang:
        return jsonify({"error": "Language parameter 'lang' is required."}), 400
    results = get_vocab_by_target_lang(current_user.id, lang)
    return jsonify([
        {
            "id": row[0], "original_word": row[1], "translated_word": row[2],
            "source_lang": row[3], "target_lang": row[4],
            "original_sentence": row[5], "translated_sentence": row[6],
            "created_at": row[7]
        } for row in results
    ])

@app.route("/search-vocab", methods=["GET"])
@login_required
def search_vocab_route():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    results = search_vocab_advanced(current_user.id, query)
    return jsonify(results)

@app.route("/suggest-vocab", methods=["GET"])
@login_required
def suggest_vocab_route():
    query = request.args.get("q", "").lower()
    if not query or len(query) < 2:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT original_word FROM vocabulary WHERE user_id = ? AND original_word LIKE ?
        UNION
        SELECT DISTINCT translated_word FROM vocabulary WHERE user_id = ? AND translated_word LIKE ?
    """, (current_user.id, f"{query}%", current_user.id, f"{query}%"))
    # Sätze für Vorschläge zu durchsuchen kann sehr viele Ergebnisse liefern und ist oft nicht gewünscht.
    # Konzentriere dich auf Wörter.
    all_texts_tuples = cursor.fetchall()
    conn.close()

    words = set()
    for row_tuple in all_texts_tuples:
        if row_tuple[0]:
            words.add(row_tuple[0])

    return jsonify(sorted(list(words))[:10])


# --- Quiz Routen ---

@app.route("/run-quiz-terminal")
def run_quiz_terminal_route():
    # start_vocab_quiz(current_user.id) # Angenommen, die Funktion wird angepasst
    return "✅ Vokabelquiz wurde im Terminal gestartet (Benutzerspezifisch, wenn start_vocab_quiz angepasst wird)!"


@app.route("/quiz-data")
@login_required
def quiz_data_route():
    lang_filter = request.args.get("lang")
    num_questions = int(request.args.get("num", 10))

    vocab_list_tuples = get_vocab_for_quiz(current_user.id, limit=num_questions)

    results = []
    from vocab_quiz.quiz_engine import generate_example_sentence
    for row_tuple in vocab_list_tuples:
        lang_code_for_sentence = row_tuple[3].split("-")[0] if row_tuple[3] else "en"
        example_sentence = generate_example_sentence(row_tuple[1], lang_code_for_sentence)

        results.append({
            "id": row_tuple[0],
            "original_word": row_tuple[1],
            "translated_word": row_tuple[2],
            "source_lang": row_tuple[3],
            "target_lang": row_tuple[4],
            "original_sentence": row_tuple[5],
            "translated_sentence": row_tuple[6],
            "example_sentence_generated": example_sentence
        })
    return jsonify(results)


@app.route("/evaluate-answer", methods=["POST"])
@login_required
def evaluate_answer():
    try:
        data = request.get_json()
        result = evaluate_translation_with_gemini(
            data["source_sentence"], data["user_translation"],
            data["expected_word"], data["target_lang"]
        )
        if not result: return jsonify({"feedback": "⚠️ Fehler bei der Bewertung"}), 200
        return jsonify({"feedback": result}), 200
    except Exception as e:
        print(f"❌ Bewertungsfehler: {str(e)}")
        return jsonify({"feedback": "⚠️ Fehler bei der Bewertung"}), 500


@app.route("/save-result", methods=["POST"])
@login_required
def save_result_route():
    data = request.get_json()
    try:
        save_quiz_result(
            current_user.id,
            language=data.get("language", "unbekannt"),
            vocab_score=int(data.get("vocab_score", 0)),
            sentence_score=int(data.get("sentence_score", 0)),
            total_score=int(data.get("total_score", 0)),
            passed=bool(data.get("passed", False))
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Dashboard / Statistik Routen ---

@app.route("/learning-activity-over-time")
@login_required
def learning_activity_route():
    data = get_learning_activity_over_time(current_user.id)
    return jsonify(data)

@app.route("/language-level-stats")
@login_required
def language_level_stats_route():
    data = get_language_levels(current_user.id)
    return jsonify(data)

@app.route("/vocab-language-stats")
@login_required
def vocab_language_stats_route():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_lang, COUNT(*)
        FROM vocabulary
        WHERE user_id = ?
        GROUP BY target_lang
    """, (current_user.id,))
    data_tuples = cursor.fetchall()
    conn.close()
    return jsonify({
        "labels": [row[0] for row in data_tuples],
        "counts": [row[1] for row in data_tuples]
    })

@app.route("/quiz-result-summary")
@login_required
def quiz_result_summary_route():
    stats = get_summary_stats(current_user.id)
    failed_tests = stats["total_tests"] - stats["passed_tests"]
    return jsonify({"passed": stats["passed_tests"], "failed": failed_tests})


@app.route("/dashboard-kpis")
@login_required
def dashboard_kpis_route():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ?", (current_user.id,))
    total_tests = (cursor.fetchone() or (0,))[0]

    cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (current_user.id,))
    total_vocab = (cursor.fetchone() or (0,))[0]

    cursor.execute("SELECT AVG(total_score) FROM quiz_results WHERE user_id = ?", (current_user.id,))
    avg_score = (cursor.fetchone() or (0,))[0] or 0

    cursor.execute("SELECT total_score FROM quiz_results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user.id,))
    last_score_row = cursor.fetchone()
    last_score = last_score_row[0] if last_score_row else 0
    conn.close()
    return jsonify({
        "total_tests": total_tests, "total_vocab": total_vocab,
        "avg_score": round(avg_score), "last_score": round(last_score)
    })

# --- Lern-Engine Routen ---

@app.route("/get-learn-vocab", methods=["GET"])
@login_required
def get_learn_vocab_route():
    vocab = le_get_next_vocab(current_user.id)
    if vocab is None:
        return jsonify({"done": True, "message": "🎉 Du hast alle Vokabeln dieser Session gelernt oder es sind keine verfügbar!"})
    return jsonify(vocab)

@app.route("/submit-vocab-result", methods=["POST"])
@login_required
def submit_vocab_result_route():
    data = request.get_json()
    vocab_id = data.get("id")
    result_status = data.get("result")

    if vocab_id is None or not result_status:
        return jsonify({"status": "error", "message": "Ungültige Daten: vocab_id und result werden benötigt."}), 400

    try:
        le_update_learning_progress(current_user.id, vocab_id, result_status)
        achieved = le_check_daily_goal_achieved(current_user.id)
        return jsonify({"status": "success", "goal_achieved": achieved})
    except Exception as e:
        app.logger.error(f"Fehler in /submit-vocab-result: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/reset-learn-session", methods=["POST"])
@login_required
def reset_learn_session_route():
    le_reset_session(current_user.id)
    return jsonify({"status": "reset"})

@app.route("/start-session", methods=["POST"])
@login_required
def start_session_route():
    try:
        le_start_new_session(current_user.id)
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Fehler in /start-session: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/learning-progress", methods=["GET"])
@login_required
def learning_progress_route():
    progress = le_get_session_progress(current_user.id)
    return jsonify(progress)


# --- Main Guard ---
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    os.makedirs("speech_module", exist_ok=True)
    app.run(debug=True, port=5000)