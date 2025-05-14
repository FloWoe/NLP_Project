import google.generativeai as genai
import spacy
from nltk.stem.snowball import SnowballStemmer
from configuration.config import GEMINI_API_KEY
from Translation.translator import translate_text  # Für Google Translate

# ✅ Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Sprachmodelle laden
nlp_models = {
    "de": spacy.load("de_core_news_sm"),
    "en": spacy.load("en_core_web_sm"),
    "fr": spacy.load("fr_core_news_sm"),
    "es": spacy.load("es_core_news_sm"),
    "ja": spacy.load("ja_core_news_sm"),
    "it": spacy.load("it_core_news_sm"),
    "pt": spacy.load("pt_core_news_sm"),
    "el": spacy.load("el_core_news_sm"),
    "nl": spacy.load("nl_core_news_sm"),
    "sv": spacy.load("sv_core_news_sm"),
    "no": spacy.load("nb_core_news_sm"),
    "da": spacy.load("da_core_news_sm"),
    "fi": spacy.load("fi_core_news_sm"),
    "pl": spacy.load("pl_core_news_sm"),
    "cs": spacy.load("xx_ent_wiki_sm"),
    "sk": spacy.load("xx_ent_wiki_sm"),
    "hu": spacy.load("xx_ent_wiki_sm"),
    "ro": spacy.load("ro_core_news_sm"),
    "bg": spacy.load("xx_ent_wiki_sm"),
    "sr": spacy.load("xx_ent_wiki_sm"),
    "hr": spacy.load("hr_core_news_sm"),
    "sq": spacy.load("xx_ent_wiki_sm"),
    "ru": spacy.load("ru_core_news_sm"),
    "uk": spacy.load("uk_core_news_sm"),
}

stemmer_map = {
    "en": SnowballStemmer("english"),
    "de": SnowballStemmer("german"),
    "fr": SnowballStemmer("french"),
    "es": SnowballStemmer("spanish"),
    "it": SnowballStemmer("italian"),
    "pt": SnowballStemmer("portuguese")
}

def stem(word: str, lang_code: str) -> str:
    stemmer = stemmer_map.get(lang_code)
    return stemmer.stem(word.lower()) if stemmer else word.lower()

def lemmatize(word: str, lang_code: str, sentence: str = None) -> str:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return word.lower()
    doc = nlp(sentence if sentence else word)
    for token in doc:
        if token.text.lower() == word.lower():
            return token.lemma_.lower()
    return word.lower()

def get_pos_tag(word: str, lang_code: str, sentence: str = None) -> str:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return ""
    doc = nlp(sentence if sentence else word)
    for token in doc:
        if token.text.lower() == word.lower():
            return token.pos_
    return ""

def find_all_words_with_same_lemma(text: str, lemma: str, lang_code: str) -> list:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return []
    doc = nlp(text)
    return [token.text for token in doc if token.lemma_.lower() == lemma.lower()]

def is_article_by_stem(word: str, lang_code: str) -> bool:
    known_article_stems = {
        "en": ["the", "a", "an"],
        "de": ["der", "die", "das", "ein", "eine", "einer", "einen", "einem"],
        "fr": ["le", "la", "les", "un", "une", "des"],
        "es": ["el", "la", "los", "las", "un", "una"],
        "it": ["il", "lo", "la", "i", "gli", "le", "un", "una"],
        "pt": ["o", "a", "os", "as", "um", "uma"]
    }
    return stem(word, lang_code) in [stem(w, lang_code) for w in known_article_stems.get(lang_code, [])]

def is_verb_only(phrase: str, lang_code: str) -> bool:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return False
    doc = nlp(phrase)
    return all(token.pos_ in ["VERB", "AUX"] for token in doc if token.text.strip())

def remove_articles(phrase: str, lang_code: str) -> str:
    words = phrase.strip().split()
    return " ".join(w for w in words if not is_article_by_stem(w, lang_code))

def extract_lemmas_from_phrase(phrase: str, lang_code: str) -> list:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return []
    doc = nlp(phrase)
    return [token.lemma_.lower() for token in doc if token.pos_ in ["VERB", "AUX", "NOUN", "ADJ"]]

# 🧠 Wortvergleich basierend auf echter Google-Übersetzung
def align_selected_word(original_sentence, selected_word, source_lang_code, target_lang_code):
    translation_result = translate_text(original_sentence, target_lang_code)
    translated_sentence = translation_result["translated"]
    return find_matching_word_crosslingual(
        sentence_lang1=original_sentence,
        sentence_lang2=translated_sentence,
        selected_word=selected_word,
        source_lang=source_lang_code,
        target_lang=target_lang_code
    )

# 🧠 Gemini-basierter Matching-Vergleich
def find_matching_word_crosslingual(
    sentence_lang1: str,
    sentence_lang2: str,
    selected_word: str,
    source_lang: str,
    target_lang: str,
    include_auxiliary: bool = True
):
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    try:
        is_selected_article = is_article_by_stem(selected_word, source_lang)
        pos_tag = get_pos_tag(selected_word, source_lang, sentence_lang1)

        prompt = (
            f"Ein Wort wurde markiert: „{selected_word}“\n"
            f"📘 Originalsatz ({source_lang}): \"{sentence_lang1}\"\n"
            f"📗 Zielsatz ({target_lang}): \"{sentence_lang2}\"\n\n"
            f"👉 Gib das passende Wort oder die Wortgruppe im ZIELSATZ zurück – keine Erklärungen, keine Varianten."
        )

        gemini_response = model.generate_content(prompt)
        matched_word_raw = gemini_response.text.strip()
        matched_word_list = [w.strip() for w in matched_word_raw.split(",") if w.strip()]

        selected_lemma = lemmatize(selected_word, source_lang, sentence_lang1)
        original_matches = find_all_words_with_same_lemma(sentence_lang1, selected_lemma, source_lang)

        translated_matches = []
        matched_lemmas = []

        if is_selected_article:
            # 🔥 Hole ALLE Artikel aus dem Zieltext – nicht nur die von Gemini
            translated_matches = [
                token.text for token in nlp_models[target_lang](sentence_lang2)
                if is_article_by_stem(token.text, target_lang)
            ]
        else:
            for word in matched_word_list:
                word_clean = word if is_verb_only(word, target_lang) else remove_articles(word, target_lang)
                lemmas = extract_lemmas_from_phrase(word_clean, target_lang)
                for lemma in lemmas:
                    matched_lemmas.append(lemma)
                    translated_matches += find_all_words_with_same_lemma(sentence_lang2, lemma, target_lang)

        match_success = any(
            word.lower() in sentence_lang2.lower()
            or word.lower() in [w.lower() for w in translated_matches]
            for word in matched_word_list
        )

        if not translated_matches and any(w.lower() in sentence_lang2.lower() for w in matched_word_list):
            translated_matches += matched_word_list

        return {
            "selected_word": selected_word,
            "selected_lemma": selected_lemma,
            "pos_tag": pos_tag,
            "matched_word": matched_word_raw,
            "matched_word_cleaned": ", ".join(matched_word_list),
            "matched_lemma": ", ".join(matched_lemmas),
            "original_matches": original_matches,
            "translated_matches": translated_matches,
            "match_success": match_success
        }

    except Exception as e:
        return {"error": f"(Fehler bei Gemini: {e})"}
