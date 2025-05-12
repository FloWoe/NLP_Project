import google.generativeai as genai
import spacy
from configuration.config import GEMINI_API_KEY

# ✅ Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Sprachmodelle laden
nlp_models = {
    "de": spacy.load("de_core_news_sm"),        # Deutsch
    "en": spacy.load("en_core_web_sm"),          # Englisch
    "fr": spacy.load("fr_core_news_sm"),         # Französisch
    "es": spacy.load("es_core_news_sm"),         # Spanisch
    "ja": spacy.load("ja_core_news_sm"),         # Japanisch
    "it": spacy.load("it_core_news_sm"),         # Italienisch
    "pt": spacy.load("pt_core_news_sm"),         # Portugiesisch
    "el": spacy.load("el_core_news_sm"),         # Griechisch
    "nl": spacy.load("nl_core_news_sm"),         # Niederländisch
    "sv": spacy.load("sv_core_news_sm"),         # Schwedisch
    "no": spacy.load("nb_core_news_sm"),         # Norwegisch Bokmål
    "da": spacy.load("da_core_news_sm"),         # Dänisch
    "fi": spacy.load("fi_core_news_sm"),         # Finnisch
    "pl": spacy.load("pl_core_news_sm"),         # Polnisch
    "cs": spacy.load("xx_ent_wiki_sm"),          # Tschechisch (kein natives Modell)
    "sk": spacy.load("xx_ent_wiki_sm"),          # Slowakisch (kein natives Modell)
    "hu": spacy.load("xx_ent_wiki_sm"),          # Ungarisch (kein natives Modell)
    "ro": spacy.load("ro_core_news_sm"),         # Rumänisch
    "bg": spacy.load("xx_ent_wiki_sm"),          # Bulgarisch (kein natives Modell)
    "sr": spacy.load("xx_ent_wiki_sm"),          # Serbisch (kein natives Modell)
    "hr": spacy.load("hr_core_news_sm"),         # Kroatisch
    "sq": spacy.load("xx_ent_wiki_sm"),          # Albanisch (kein natives Modell)
    "ru": spacy.load("ru_core_news_sm"),         # Russisch
    "uk": spacy.load("uk_core_news_sm"),         # Ukrainisch
}


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
    """Gibt die POS-Kategorie des Wortes zurück (z. B. NOUN, VERB, etc.)"""
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


def find_matching_chunk(text: str, phrase: str, lang_code: str) -> bool:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return False
    doc = nlp(text)
    return any(phrase.lower() == chunk.text.lower() for chunk in doc.noun_chunks)


def is_article(word: str, lang_code: str) -> bool:
    articles = {
        "en": ["the", "a", "an"],
        "de": ["der", "die", "das", "ein", "eine", "einen", "einem", "einer"],
        "fr": ["le", "la", "les", "un", "une", "des"],
        "es": ["el", "la", "los", "las", "un", "una"],
        "ja": []
    }
    return word.lower() in articles.get(lang_code, [])


def is_verb_only(phrase: str, lang_code: str) -> bool:
    nlp = nlp_models.get(lang_code)
    if not nlp:
        return False
    doc = nlp(phrase)
    return all(token.pos_ in ["VERB", "AUX"] for token in doc if token.text.strip())


def remove_articles(phrase: str, lang_code: str) -> str:
    articles = {
        "en": ["the", "a", "an"],
        "de": ["der", "die", "das", "ein", "eine", "einen", "einem", "einer"],
        "fr": ["le", "la", "les", "un", "une", "des"],
        "es": ["el", "la", "los", "las", "un", "una"],
        "ja": []
    }
    words = phrase.strip().split()
    filtered = [w for w in words if w.lower() not in articles.get(lang_code, [])]
    return " ".join(filtered)


def find_matching_word_crosslingual(
    sentence_lang1: str,
    sentence_lang2: str,
    selected_word: str,
    source_lang: str,
    target_lang: str,
    include_auxiliary: bool = True
):
    """Führt eine sprachsensitive, POS- und lemma-basierte Gemini-Auswertung durch."""
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    try:
        is_selected_article = is_article(selected_word, source_lang)
        pos_tag = get_pos_tag(selected_word, source_lang, sentence_lang1)

        # 📌 Dynamischer Prompt
        if is_selected_article:
            prompt = (
                f"In folgendem Satz wurde der Artikel „{selected_word}“ markiert:\n\n"
                f"📘 Ausgangssatz ({source_lang}): \"{sentence_lang1}\"\n"
                f"📗 Zielsatz ({target_lang}): \"{sentence_lang2}\"\n\n"
                f"👉 Gib **nur den entsprechenden Artikel oder die Artikelgruppe** im Zielsatz zurück.\n"
                f"Keine Varianten, keine Erklärungen."
            )
        elif include_auxiliary and pos_tag == "VERB":
            prompt = (
                f"In folgendem Satz wurde das Verb „{selected_word}“ markiert:\n\n"
                f"📘 Ausgangssatz ({source_lang}): \"{sentence_lang1}\"\n"
                f"📗 Zielsatz ({target_lang}): \"{sentence_lang2}\"\n\n"
                f"👉 Gib die **grammatikalisch vollständige Verbform oder Wortgruppe** im Zielsatz zurück,\n"
                f"die dem markierten Verb entspricht – auch wenn das Subjekt nur implizit vorhanden ist.\n"
                f"✅ Die Antwort darf Hilfsverben, Zeitformen oder zusammengesetzte Formen enthalten.\n"
                f"Nur ein Ausdruck, keine Varianten oder Erklärungen."
            )
        else:
            prompt = (
                f"In folgendem Satz wurde das Wort „{selected_word}“ markiert:\n\n"
                f"📘 Ausgangssatz ({source_lang}): \"{sentence_lang1}\"\n"
                f"📗 Zielsatz ({target_lang}): \"{sentence_lang2}\"\n\n"
                f"👉 Gib das **inhaltlich passende einzelne Wort oder die relevante Wortgruppe** im Zielsatz zurück.\n"
                f"❌ Vermeide Hilfsverben, Artikel, Modalverben und Funktionswörter.\n"
                f"✅ Gib nur einen einzigen konkreten Ausdruck zurück – ohne Varianten oder Erklärungen."
            )

        # 🧠 Anfrage an Gemini
        gemini_response = model.generate_content(prompt)
        matched_word_raw = gemini_response.text.strip()

        # 🧠 Liste aller Gemini-Vorschläge extrahieren
        matched_word_list = [w.strip() for w in matched_word_raw.split(",")]

        # 🔠 Lemmatisierung
        selected_lemma = lemmatize(selected_word, source_lang, sentence_lang1)
        original_matches = find_all_words_with_same_lemma(sentence_lang1, selected_lemma, source_lang)

        translated_matches = []
        matched_lemmas = []

        for word in matched_word_list:
            if is_selected_article or is_verb_only(word, target_lang):
                word_clean = word
            else:
                word_clean = remove_articles(word, target_lang)

            lemma = lemmatize(word_clean, target_lang, sentence_lang2)
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

