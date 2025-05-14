import sqlite3
from dataclasses import dataclass
from rapidfuzz import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz.distance import Levenshtein

# 🔹 Datenmodell
@dataclass
class VocabEntry:
    original_word: str
    translated_word: str
    source_lang: str
    target_lang: str
    original_sentence: str
    translated_sentence: str

# 🔹 Initialisieren
def init_db():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_word TEXT,
            translated_word TEXT,
            source_lang TEXT,
            target_lang TEXT,
            original_sentence TEXT,
            translated_sentence TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# 🔹 Speichern
def save_vocab(entry: VocabEntry):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vocabulary (
            original_word, translated_word,
            source_lang, target_lang,
            original_sentence, translated_sentence
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        entry.original_word, entry.translated_word,
        entry.source_lang, entry.target_lang,
        entry.original_sentence, entry.translated_sentence
    ))
    conn.commit()
    conn.close()

# 🔹 Alle Vokabeln abrufen
# 🔹 Vokabeln nach Zielsprache filtern
def get_vocab_by_target_lang(lang_code: str):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence, created_at
        FROM vocabulary
        WHERE target_lang LIKE ?
        ORDER BY created_at DESC
    """, (f"{lang_code}%",))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_vocab():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence, created_at
        FROM vocabulary
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


import random

# 🔹 Zufällige Vokabel abrufen
def get_random_vocab_entry() -> VocabEntry | None:
    all_vocab = get_all_vocab()
    if not all_vocab:
        return None
    row = random.choice(all_vocab)
    return VocabEntry(
        original_word=row[1],
        translated_word=row[2],
        source_lang=row[3],
        target_lang=row[4],
        original_sentence=row[5],
        translated_sentence=row[6]
    )
    
from rapidfuzz import fuzz

def search_vocab_advanced(query: str, top_k=15):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, original_sentence, translated_sentence
        FROM vocabulary
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    texts = [f"{r[1]} {r[2]} {r[3]} {r[4]}" for r in rows]

    # TF-IDF Ähnlichkeit vorbereiten
    vectorizer = TfidfVectorizer().fit(texts + [query])
    tfidf_matrix = vectorizer.transform(texts + [query])
    cosine_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

    query_lower = query.lower()

    for idx, row in enumerate(rows):
        original_word = row[1].lower()
        translated_word = row[2].lower()
        original_sent = row[3].lower()
        translated_sent = row[4].lower()

        # Levenshtein-Distanz (auf Wörter)
        lev_word_score = 1 / (1 + min(
            Levenshtein.distance(query_lower, original_word),
            Levenshtein.distance(query_lower, translated_word)
        ))

        # Levenshtein-Distanz (auf Sätze)
        lev_sent_score = 1 / (1 + min(
            Levenshtein.distance(query_lower, original_sent),
            Levenshtein.distance(query_lower, translated_sent)
        ))

        # Zusätzlicher Bonus bei direktem Vorkommen
        substring_bonus = 0
        if query_lower in original_sent or query_lower in translated_sent:
            substring_bonus = 0.2

        # Neue Gewichtung: Fokus auf Satzinhalt
        combined_score = (
            0.1 * lev_word_score +
            0.1 * lev_sent_score +
            0.8 * cosine_scores[idx] +
            substring_bonus
        )

        results.append((combined_score, row))

    best = sorted(results, key=lambda x: x[0], reverse=True)[:top_k]

    return [dict(
        id=r[1][0],
        original_word=r[1][1],
        translated_word=r[1][2],
        original_sentence=r[1][3],
        translated_sentence=r[1][4]
    ) for r in best if r[0] > 0.05]

    

def get_vocab_for_quiz():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang, 
               original_sentence, translated_sentence
        FROM vocabulary
        ORDER BY RANDOM()
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
