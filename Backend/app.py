from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  
from Translation.translator import translate_text
from word_finding.word_alignment import find_matching_word_crosslingual
from word_explain.Explain import explain_word
from speech_module.stt_whisper import transcribe_audio
#from speech_module.tts_Google import synthesize_speech
from speech_module.tts_Elevenlab import synthesize_speech
import google.generativeai as genai
import os
from flask import send_file
from generate_text.text_generator import generate_text_by_language
from generate_text.gap_generator import create_gap_text_with_gemini
from Backend.vocab_db import init_db, VocabEntry, save_vocab,  get_all_vocab, sqlite3
from vocab_quiz.quiz_engine import start_vocab_quiz, evaluate_translation_with_gemini




app = Flask(__name__)
CORS(app)  # ✅ Aktiviert CORS für alle Routen
init_db()

@app.route("/")
def index():
    return render_template("index.html")


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
        conn = sqlite3.connect("vocab.db")
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
        conn = sqlite3.connect("vocab.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vocabulary")
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/quiz")
def run_quiz():
    start_vocab_quiz()
    return "✅ Vokabelquiz wurde im Terminal gestartet!"

    
@app.route("/quiz-data")
def quiz_data():
    from vocab_quiz.quiz_engine import fetch_vocab_from_db, generate_example_sentence

    vocab_list = fetch_vocab_from_db()
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
    data = request.json
    source_sentence = data.get("source_sentence")
    user_translation = data.get("user_translation")
    expected_word = data.get("expected_word")
    target_lang = data.get("target_lang")

    if not all([source_sentence, user_translation, expected_word, target_lang]):
        return jsonify({"error": "❌ Fehlende Daten im Request"}), 400

    try:
        feedback = evaluate_translation_with_gemini(
            source_sentence, user_translation, expected_word, target_lang
        )
        return jsonify({"feedback": feedback})
    except Exception as e:
        return jsonify({"error": f"Gemini-Fehler: {str(e)}"}), 500





if __name__ == "__main__":
    app.run(debug=True)