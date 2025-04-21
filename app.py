from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # ✅ NEU
from Translation.translator import translate_text

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

if __name__ == "__main__":
    app.run(debug=True)

