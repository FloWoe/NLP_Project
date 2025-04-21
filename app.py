from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  
from Translation.translator import translate_text
from word_finding.word_alignment import find_matching_word_crosslingual
from word_explain.Explain import explain_word


app = Flask(__name__)
CORS(app)  # ✅ Aktiviert CORS für alle Routen

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target_lang", "en")

    try:
        translated = translate_text(text, target_lang)
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/match-word", methods=["POST"])
def match_word():
    data = request.json
    sentence1 = data.get("sentence1")
    sentence2 = data.get("sentence2")
    selected_word = data.get("selectedWord")
    selected_from = data.get("selectedFrom")  # "lang1" oder "lang2"

    try:
        matched_word = find_matching_word_crosslingual(
            sentence_lang1=sentence1,
            sentence_lang2=sentence2,
            selected_word=selected_word,
            selected_language_code=selected_from
        )
        return jsonify({"matchedWord": matched_word})
    except Exception as e:
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

if __name__ == "__main__":
    app.run(debug=True)
