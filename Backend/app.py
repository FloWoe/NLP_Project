# app.py

import os
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for # flash entfernt, da wir JSON-Antworten nutzen
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Deine Modul-Imports (unverändert)
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
    get_language_levels, get_random_vocab_entry,
    create_user, get_user_by_username, get_user_by_id, get_user_by_email,
    delete_vocab_entry, delete_all_user_vocab,
    get_vocab_entry_by_id,
    sqlite3, # Obwohl hier nicht direkt verwendet, hattest du es importiert
    get_vocab_for_quiz,
    check_password_hash
)

# Imports für learning_engine
from learning.learning_engine import (
    start_new_session as le_start_new_session,
    get_next_vocab as le_get_next_vocab,
    update_learning_progress as le_update_learning_progress,
    check_daily_goal_achieved as le_check_daily_goal_achieved,
    get_session_progress as le_get_session_progress,
    reset_session as le_reset_session
)


# --- App Konfiguration ---
template_path = os.path.join(os.path.dirname(__file__), "..", "templates")
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Wird für DB_PATH verwendet
DB_PATH = os.path.join(BASE_DIR, "..", "Database", "vocab.db") # Wird von vocab_db.py genutzt

app = Flask(__name__, template_folder=template_path, static_folder=static_path)
# WICHTIG: Setze einen starken, zufälligen Secret Key!
# Am besten über Umgebungsvariable: os.environ.get('FLASK_SECRET_KEY', 'default_entwicklung_key')
app.config['SECRET_KEY'] = 'dein-super-geheimer-schluessel-unbedingt-aendern!'
CORS(app)

# --- Flask-Login Konfiguration ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Name der Login-Route, zu der umgeleitet wird
# login_manager.login_message = "Bitte melde dich an, um diese Seite zu sehen." # Standardnachricht
# login_manager.login_message_category = "info" # Bootstrap-Klasse für die Nachricht

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(id=user_data[0], username=user_data[1], email=user_data[2])
    return None

# --- Datenbank Initialisierung ---
# Diese sollten nur einmal beim Start aufgerufen werden oder wenn die DB nicht existiert.
# In einer Produktivumgebung würdest du Migrationswerkzeuge wie Flask-Migrate verwenden.
init_user_table()
init_db()
init_result_table()
init_learning_table()
init_learning_progress_table()


# --- Authentifizierungs-Routen ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) # Oder wohin auch immer eingeloggte User sollen

    if request.method == 'POST':
        data = request.get_json()
        if not data:
             return jsonify({"status": "error", "message": "Keine Daten im Request Body."}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "Benutzername, Email und Passwort sind erforderlich."}), 400
        if len(password) < 6:
             return jsonify({"status": "error", "message": "Das Passwort muss mindestens 6 Zeichen lang sein."}), 400
        if get_user_by_username(username):
            return jsonify({"status": "error", "message": "Benutzername existiert bereits."}), 409 # Conflict
        if get_user_by_email(email):
            return jsonify({"status": "error", "message": "Email-Adresse ist bereits registriert."}), 409 # Conflict

        user_id = create_user(username, email, password)
        if user_id:
            user_data = get_user_by_id(user_id) # Hole User-Daten für Login
            user_obj = User(id=user_data[0], username=user_data[1], email=user_data[2])
            login_user(user_obj) # Benutzer nach Registrierung direkt einloggen
            return jsonify({"status": "success", "message": "Registrierung erfolgreich! Du bist jetzt eingeloggt."})
        else:
            return jsonify({"status": "error", "message": "Registrierung fehlgeschlagen. Bitte versuche es erneut."}), 500
    
    # Für GET-Request: Zeige das Registrierungsformular an
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) # Eingeloggte User zum Dashboard

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten im Request Body."}), 400
            
        login_identifier = data.get('login_identifier')
        password = data.get('password')
        remember = data.get('remember', False)

        if not login_identifier or not password:
            return jsonify({"status": "error", "message": "Benutzername/Email und Passwort sind erforderlich."}), 400

        # Versuche, den User per Username oder Email zu finden
        user_data = get_user_by_username(login_identifier)
        if not user_data:
            user_data = get_user_by_email(login_identifier)

        if user_data and check_password_hash(user_data[3], password): # Index 3 ist password_hash
            user_obj = User(id=user_data[0], username=user_data[1], email=user_data[2])
            login_user(user_obj, remember=remember)
            return jsonify({"status": "success", "message": f"Login erfolgreich! Willkommen, {user_obj.username}!"})
        else:
            return jsonify({"status": "error", "message": "Ungültiger Benutzername/Email oder Passwort."}), 401 # Unauthorized
            
    # Für GET-Request: Zeige das Login-Formular an
    return render_template('login.html')

@app.route('/logout')
@login_required # Nur eingeloggte Benutzer können sich ausloggen
def logout():
    logout_user()
    return jsonify({"status": "success", "message": "Du wurdest erfolgreich ausgeloggt."})
    # Normalerweise würdest du hier zum Login oder zur Homepage weiterleiten,
    # aber da dein JS die Weiterleitung nach der JSON-Antwort macht, ist das hier ok.
    # Alternativ: return redirect(url_for('login')) direkt hier.

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

# --- Index / Landing Page Route ---
@app.route("/")
def index():
    if current_user.is_authenticated:
        # Hierhin wird der User nach dem Login oder bei Aufruf von "/" geleitet, wenn eingeloggt.
        # Deine `index.html` ist die Übersetzer-App. Das ist okay.
        return render_template("index.html") 
    else:
        # Nicht eingeloggte User werden zur Login-Seite geleitet.
        return redirect(url_for('login'))


# --- Deine bestehenden Seiten-Routen (Dashboard, Favoriten etc.) ---
# Die `@login_required` Dekoratoren sind hier korrekt.

@app.route("/quiz") # Die HTML-Seite für das Quiz
@login_required
def quiz_page():
    return render_template("quiz.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("Dashboard.html")

@app.route("/favorite") # Vokabelliste
@login_required
def favorite():
    return render_template("favorite.html")

@app.route("/lernen")
@login_required
def lernen():
    return render_template("lernen.html")

@app.route("/hilfe") # Hilfe kann öffentlich bleiben oder auch @login_required bekommen
def hilfe():
    return render_template("hilfe.html")


# --- API Endpunkte (Unverändert von deinem letzten Stand, da sie @login_required und current_user.id nutzen) ---
# (Hier kommt der Rest deiner API-Routen: /translate, /match-word, ..., /learning-progress)
# Stelle sicher, dass ALLE Routen, die auf benutzerspezifische Daten zugreifen oder
# Aktionen im Kontext eines Users ausführen, `@login_required` haben und `current_user.id` verwenden.

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
        # Bestimme sentence_lang1 und sentence_lang2 basierend auf selectedFrom
        selected_from = data.get("selectedFrom")
        s1 = data.get("sentence1")
        s2 = data.get("sentence2")
        
        sentence_lang1_text = s1 if selected_from == "lang1" else s2
        sentence_lang2_text = s2 if selected_from == "lang1" else s1

        source_ui_lang = data.get("sourceLangCode", "de-DE")
        target_ui_lang = data.get("targetLangCode", "en-US")

        # Bestimme source_lang und target_lang für die API basierend auf selectedFrom
        api_source_lang = source_ui_lang.split("-")[0].lower() if selected_from == "lang1" else target_ui_lang.split("-")[0].lower()
        api_target_lang = target_ui_lang.split("-")[0].lower() if selected_from == "lang1" else source_ui_lang.split("-")[0].lower()

        result = find_matching_word_crosslingual(
            sentence_lang1=sentence_lang1_text,
            sentence_lang2=sentence_lang2_text,
            selected_word=data.get("selectedWord"),
            source_lang=api_source_lang,
            target_lang=api_target_lang
        )
        if not isinstance(result, dict): return jsonify({"error": f"Ungültiges Ergebnis von word_alignment: {result}"}), 500
        if "error" in result: return jsonify({"error": result["error"]}), 500
        
        translated_matches = result.get("translated_matches", [])
        if not isinstance(translated_matches, list): # Sicherstellen, dass es eine Liste ist
            if isinstance(translated_matches, str) and translated_matches:
                 translated_matches = [translated_matches]
            else:
                 translated_matches = []


        # Format matched_word und matched_lemma für die Rückgabe
        matched_word_display = result.get("matched_word_cleaned", "") # Nutze das bereinigte Feld
        # if isinstance(result.get("matched_word"), list):
        #     matched_word_display = ", ".join(filter(None,result.get("matched_word", [])))
        # else:
        #     matched_word_display = result.get("matched_word","")
            
        matched_lemma_display = result.get("matched_lemma","")
        # if isinstance(result.get("matched_lemma"), list):
        #      matched_lemma_display = ", ".join(filter(None,result.get("matched_lemma", [])))
        # else:
        #      matched_lemma_display = result.get("matched_lemma","")


        return jsonify({
            "selectedWord": result.get("selected_word"),
            "selectedLemma": result.get("selected_lemma"),
            "matchedWord": matched_word_display,
            "matchedLemma": matched_lemma_display,
            "originalMatches": result.get("original_matches", []),
            "translatedMatches": translated_matches,
            "matchSuccess": result.get("match_success", False)
        })
    except Exception as e:
        app.logger.error(f"❌ Fehler in /match-word: {e}", exc_info=True)
        return jsonify({"error": "Ein interner Fehler ist beim Wortabgleich aufgetreten."}), 500


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
    ext = os.path.splitext(audio_file.filename)[-1].lower() if audio_file.filename else ".webm"
    speech_module_dir = "speech_module"
    os.makedirs(speech_module_dir, exist_ok=True)
    temp_path = os.path.join(speech_module_dir, f"temp_input{ext}")
    try:
        audio_file.save(temp_path)
        transcription = transcribe_audio(temp_path)
        return jsonify({"transcription": transcription})
    except Exception as e:
        app.logger.error(f"Fehler bei Transkription: {e}", exc_info=True)
        return jsonify({"error": f"Fehler bei Transkription: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e_rem:
                app.logger.error(f"Fehler beim Löschen der temp Audiodatei: {e_rem}")


@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text")
        lang = data.get("lang", "de-DE") # Sprache vom Client empfangen
        if not text: return {"error": "Kein Text angegeben"}, 400
        
        # synthesize_speech sollte den Sprachcode verarbeiten können
        output_path = synthesize_speech(text, lang=lang) 
        
        if output_path and os.path.exists(output_path):
            abs_path = os.path.abspath(output_path)
            # Wichtig: Der Pfad für send_file muss relativ zum Anwendungsverzeichnis sein,
            # oder absolut, wenn send_file korrekt konfiguriert ist (was es meist ist).
            # Wenn synthesize_speech in "Backend/output.mp3" speichert und app.py in Backend ist, dann ist output.mp3 relativ.
            return send_file(abs_path, mimetype="audio/mpeg", as_attachment=False)
        else:
            app.logger.error(f"TTS-Datei nicht gefunden oder erstellt für Text: {text[:30]}")
            return {"error": "TTS-Datei wurde nicht gefunden oder erstellt"}, 500
    except Exception as e:
        app.logger.error(f"❌ Fehler im TTS-Endpoint: {e}", exc_info=True)
        return {"error": "Ein interner Fehler ist bei der Sprachausgabe aufgetreten."}, 500

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

# --- Vokabel-spezifische Routen --- (sollten alle @login_required haben)

@app.route("/save-vocab", methods=["POST"])
@login_required
def save_vocab_route():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Keine Daten erhalten."}), 400
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
        return jsonify({"status": "error", "message": f"Fehlendes Feld: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Fehler in /save-vocab: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Fehler beim Speichern der Vokabel."}), 500

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
            # Dies könnte auch bedeuten, dass die Vokabel nicht existiert, nicht nur, dass sie nicht dem User gehört.
            return jsonify({"status": "error", "message": "Vokabel nicht gefunden oder gehört nicht zum Benutzer."}), 404
    except Exception as e:
        app.logger.error(f"Fehler in /delete-vocab: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Fehler beim Löschen der Vokabel."}), 500

@app.route("/delete-all-vocab", methods=["DELETE"])
@login_required
def delete_all_vocab_route():
    try:
        delete_all_user_vocab(current_user.id)
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Fehler in /delete-all-vocab: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Fehler beim Löschen aller Vokabeln."}), 500

@app.route("/get-vocab-by-lang")
@login_required
def get_vocab_by_lang_route():
    lang = request.args.get("lang", "")
    # Keine explizite Prüfung für leeren lang string, da vocab_db.get_vocab_by_target_lang
    # mit `LIKE ""` oder `LIKE "%"` umgehen sollte (liefert dann alle Vokabeln des Users)
    # Falls ein leerer String nicht alle liefern soll, hier prüfen:
    # if not lang:
    #     return jsonify({"error": "Language parameter 'lang' is required."}), 400
    results_tuples = get_vocab_by_target_lang(current_user.id, lang)
    return jsonify([
        {
            "id": row[0], "original_word": row[1], "translated_word": row[2],
            "source_lang": row[3], "target_lang": row[4],
            "original_sentence": row[5], "translated_sentence": row[6],
            "created_at": row[7]
        } for row in results_tuples
    ])

@app.route("/search-vocab", methods=["GET"])
@login_required
def search_vocab_route():
    query = request.args.get("q", "").strip()
    # Optional: lang Filter auch hier, wenn gewünscht
    # lang = request.args.get("lang", "")
    if not query:
        # Wenn Query leer ist, vielleicht alle Vokabeln des Users zurückgeben (oder nach Sprache filtern)?
        # Hängt von der Anforderung in favorite.html ab, wenn dort gesucht wird.
        # Aktuell gibt search_vocab_advanced eine leere Liste zurück, wenn Query leer ist.
        # Oder hier direkt get_all_vocab(current_user.id) aufrufen, wenn query leer ist.
        return jsonify([])
        
    results = search_vocab_advanced(current_user.id, query)
    return jsonify(results) # search_vocab_advanced gibt bereits Liste von Dicts zurück

@app.route("/suggest-vocab", methods=["GET"])
@login_required
def suggest_vocab_route():
    query = request.args.get("q", "").lower()
    if not query or len(query) < 2:
        return jsonify([])

    # DB-Zugriff direkt hier ist okay für diese spezielle Query, aber könnte auch in vocab_db.py
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Die Query ist spezifisch für Vorschläge basierend auf Wortanfängen
    cursor.execute("""
        SELECT DISTINCT original_word FROM vocabulary WHERE user_id = ? AND original_word LIKE ?
        UNION
        SELECT DISTINCT translated_word FROM vocabulary WHERE user_id = ? AND translated_word LIKE ?
    """, (current_user.id, f"{query}%", current_user.id, f"{query}%"))
    all_texts_tuples = cursor.fetchall()
    conn.close()

    words = set()
    for row_tuple in all_texts_tuples:
        if row_tuple[0]: # Stellt sicher, dass das Wort nicht None ist
            words.add(row_tuple[0])
    return jsonify(sorted(list(words))[:10]) # Nur die Top 10 Vorschläge

# --- Quiz Routen ---

@app.route("/run-quiz-terminal") # Diese Route ist für ein Konsolen-Quiz, wenn benötigt
@login_required # Sollte geschützt sein, wenn es User-Vokabeln nutzt
def run_quiz_terminal_route():
    # start_vocab_quiz müsste die user_id akzeptieren
    # start_vocab_quiz(current_user.id) 
    return f"✅ Vokabelquiz für User {current_user.username} wurde im Terminal gestartet (Funktion muss angepasst werden)!"


@app.route("/quiz-data")
@login_required
def quiz_data_route():
    lang_filter = request.args.get("lang") # Kann leer sein für alle Sprachen
    num_questions = int(request.args.get("num", 10))

    # get_vocab_for_quiz sollte user_id und limit verarbeiten.
    # Eine zusätzliche Filterung nach Sprache müsste in get_vocab_for_quiz (in vocab_db.py)
    # implementiert werden oder hier nachgelagert erfolgen.
    # Annahme: get_vocab_for_quiz(user_id, limit) holt Vokabeln für den User.
    # Wenn lang_filter gesetzt ist, filtern wir hier:
    
    all_user_quiz_vocab = get_vocab_for_quiz(current_user.id, limit=1000) # Hole mehr als nötig, um filtern zu können
    
    filtered_vocab_list = []
    if lang_filter:
        for v in all_user_quiz_vocab:
            # v[4] ist target_lang in der Tupelstruktur von get_vocab_for_quiz
            if v[4] and v[4].startswith(lang_filter):
                filtered_vocab_list.append(v)
    else:
        filtered_vocab_list = all_user_quiz_vocab

    # Wähle zufällig num_questions aus der gefilterten Liste
    if len(filtered_vocab_list) > num_questions:
        selected_vocab_tuples = random.sample(filtered_vocab_list, num_questions)
    else:
        selected_vocab_tuples = filtered_vocab_list


    results_for_frontend = []
    # Import von generate_example_sentence hier, um zirkuläre Abhängigkeiten zu vermeiden,
    # falls quiz_engine auch app-Kontext bräuchte (was es hier nicht tut).
    from vocab_quiz.quiz_engine import generate_example_sentence
    for row_tuple in selected_vocab_tuples:
        # Annahme der Struktur von get_vocab_for_quiz:
        # (id, original_word, translated_word, source_lang, target_lang, original_sentence, translated_sentence)
        vocab_id, original, translated, source_lang_db, target_lang_db, orig_sent, trans_sent = row_tuple

        # Sprache für Beispielsatz (basierend auf Originalsprache der Vokabel)
        lang_code_for_ex_sentence = source_lang_db.split("-")[0] if source_lang_db else "de" # Fallback
        
        example_sentence_generated = generate_example_sentence(original, lang_code_for_ex_sentence)

        results_for_frontend.append({
            "id": vocab_id,
            "original_word": original,
            "translated_word": translated,
            "source_lang": source_lang_db,
            "target_lang": target_lang_db,
            "original_sentence": orig_sent, # Beispielsatz aus DB, falls vorhanden
            "translated_sentence": trans_sent, # Beispielsatz aus DB, falls vorhanden
            "example_sentence_generated": example_sentence_generated # Neu generierter Satz
        })
    return jsonify(results_for_frontend)


@app.route("/evaluate-answer", methods=["POST"])
@login_required # Sinnvoll, da Teil eines User-Quiz
def evaluate_answer():
    data = request.get_json()
    if not data: return jsonify({"feedback": "⚠️ Keine Daten erhalten."}), 400
    try:
        # evaluate_translation_with_gemini ist eine generische Funktion
        result_feedback = evaluate_translation_with_gemini(
            data["source_sentence"], data["user_translation"],
            data["expected_word"], data["target_lang"]
        )
        if not result_feedback: # Sollte nicht passieren, da die Fkt immer String zurückgibt
             return jsonify({"feedback": "⚠️ Fehler bei der Bewertung, keine Rückgabe von KI."}), 500
        return jsonify({"feedback": result_feedback}), 200
    except KeyError as e:
        return jsonify({"feedback": f"⚠️ Fehlende Daten im Request: {e}"}), 400
    except Exception as e:
        app.logger.error(f"❌ Bewertungsfehler: {str(e)}", exc_info=True)
        return jsonify({"feedback": "⚠️ Interner Fehler bei der Bewertung."}), 500


@app.route("/save-result", methods=["POST"])
@login_required
def save_result_route():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Keine Daten erhalten."}),400
    try:
        save_quiz_result( # Diese Funktion aus vocab_db.py erwartet user_id als ersten Parameter
            current_user.id,
            language=data.get("language", "unbekannt"),
            vocab_score=int(data.get("vocab_score", 0)),
            sentence_score=int(data.get("sentence_score", 0)),
            total_score=int(data.get("total_score", 0)),
            passed=bool(data.get("passed", False))
        )
        return jsonify({"status": "success"})
    except ValueError:
         return jsonify({"status": "error", "message": "Ungültige Zahlenwerte für Scores."}), 400
    except Exception as e:
        app.logger.error(f"Fehler in /save-result: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Fehler beim Speichern des Quizergebnisses."}), 500

# --- Dashboard / Statistik Routen --- (sollten alle @login_required haben)

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
        "labels": [row[0] if row[0] else "Unbekannt" for row in data_tuples], # Fallback für None
        "counts": [row[1] for row in data_tuples]
    })

@app.route("/quiz-result-summary")
@login_required
def quiz_result_summary_route():
    stats = get_summary_stats(current_user.id) # Diese Fkt. aus vocab_db.py erwartet user_id
    failed_tests = stats.get("total_tests", 0) - stats.get("passed_tests", 0)
    return jsonify({"passed": stats.get("passed_tests", 0), "failed": failed_tests})


@app.route("/dashboard-kpis")
@login_required
def dashboard_kpis_route():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Verwende "or (0,)" um sicherzustellen, dass fetchone() nie None ist für den Indexzugriff
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ?", (current_user.id,))
    total_tests = (cursor.fetchone() or (0,))[0]

    cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (current_user.id,))
    total_vocab = (cursor.fetchone() or (0,))[0]

    cursor.execute("SELECT AVG(total_score) FROM quiz_results WHERE user_id = ?", (current_user.id,))
    avg_score_tuple = cursor.fetchone()
    avg_score = avg_score_tuple[0] if avg_score_tuple and avg_score_tuple[0] is not None else 0

    cursor.execute("SELECT total_score FROM quiz_results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user.id,))
    last_score_row = cursor.fetchone()
    last_score = last_score_row[0] if last_score_row and last_score_row[0] is not None else 0
    conn.close()
    return jsonify({
        "total_tests": total_tests, "total_vocab": total_vocab,
        "avg_score": round(avg_score), "last_score": round(last_score)
    })

# --- Lern-Engine Routen --- (sollten alle @login_required und user_id an le_funktionen übergeben)

@app.route("/get-learn-vocab", methods=["GET"])
@login_required
def get_learn_vocab_route():
    # le_get_next_vocab (aus learning_engine.py) erwartet user_id
    vocab = le_get_next_vocab(current_user.id)
    if vocab is None:
        return jsonify({"done": True, "message": "🎉 Du hast alle Vokabeln dieser Session gelernt oder es sind keine verfügbar!"})
    return jsonify(vocab) # vocab sollte bereits ein Dict sein

@app.route("/submit-vocab-result", methods=["POST"])
@login_required
def submit_vocab_result_route():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Keine Daten erhalten."}),400
    
    vocab_id = data.get("id")       # ID der Vokabel
    result_status = data.get("result") # "known", "partial", "unknown"

    if vocab_id is None or not result_status:
        return jsonify({"status": "error", "message": "Ungültige Daten: vocab_id und result werden benötigt."}), 400

    try:
        # le_update_learning_progress (aus learning_engine.py) erwartet user_id, vocab_id, result_status
        le_update_learning_progress(current_user.id, int(vocab_id), result_status)
        # le_check_daily_goal_achieved (aus learning_engine.py) erwartet user_id
        achieved = le_check_daily_goal_achieved(current_user.id)
        return jsonify({"status": "success", "goal_achieved": achieved})
    except ValueError:
        return jsonify({"status": "error", "message": "Ungültige Vokabel-ID."}), 400
    except Exception as e:
        app.logger.error(f"Fehler in /submit-vocab-result: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Interner Fehler beim Verarbeiten des Ergebnisses."}), 500


@app.route("/reset-learn-session", methods=["POST"])
@login_required
def reset_learn_session_route():
    # le_reset_session (aus learning_engine.py) erwartet user_id
    le_reset_session(current_user.id)
    return jsonify({"status": "reset"})

@app.route("/start-session", methods=["POST"]) # Startet eine neue Lernsession
@login_required
def start_session_route():
    try:
        # le_start_new_session (aus learning_engine.py) erwartet user_id
        le_start_new_session(current_user.id)
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Fehler in /start-session: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Interner Fehler beim Starten der Session."}), 500

@app.route("/learning-progress", methods=["GET"])
@login_required
def learning_progress_route():
    # le_get_session_progress (aus learning_engine.py) erwartet user_id
    progress = le_get_session_progress(current_user.id)
    return jsonify(progress)


# --- Main Guard ---
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO) # Basis-Logging konfigurieren
    # Sicherstellen, dass das Verzeichnis für temporäre Audiodateien existiert
    os.makedirs("speech_module", exist_ok=True)
    # Ausgabeordner für TTS, falls noch nicht global konfiguriert
    # os.makedirs(os.path.join("Backend", "audio_output"), exist_ok=True) # Beispiel
    
    app.run(debug=True, port=5000)