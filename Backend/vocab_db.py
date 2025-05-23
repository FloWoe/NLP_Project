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
    from rapidfuzz.distance import Levenshtein

    query_lower = query.lower()
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, original_sentence, translated_sentence
        FROM vocabulary
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []

    for row in rows:
        original_word = row[1].lower()
        translated_word = row[2].lower()

        # Levenshtein-Distanz nur auf die beiden Wörter (nicht Sätze!)
        lev_dist = min(
            Levenshtein.distance(query_lower, original_word),
            Levenshtein.distance(query_lower, translated_word)
        )

        max_len = max(len(query_lower), len(original_word), len(translated_word))
        similarity_score = 1 - (lev_dist / max_len)  # normalisiert

        if similarity_score >= 0.6:  # Schwelle: wie unscharf erlaubt ist
            results.append((similarity_score, row))

    best = sorted(results, key=lambda x: x[0], reverse=True)[:top_k]

    return [dict(
        id=r[1][0],
        original_word=r[1][1],
        translated_word=r[1][2],
        original_sentence=r[1][3],
        translated_sentence=r[1][4]
    ) for r in best]


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

def init_result_table():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            vocab_score INTEGER,
            sentence_score INTEGER,
            total_score INTEGER,
            passed BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_quiz_result(language: str, vocab_score: int, sentence_score: int, total_score: int, passed: bool):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_results (
            language, vocab_score, sentence_score, total_score, passed
        ) VALUES (?, ?, ?, ?, ?)
    """, (language, vocab_score, sentence_score, total_score, passed))
    conn.commit()
    conn.close()

def get_all_results():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT language, vocab_score, sentence_score, total_score, passed, timestamp
        FROM quiz_results
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_summary_stats():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quiz_results")
    total_tests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE passed = 1")
    passed_tests = cursor.fetchone()[0]

    conn.close()
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
    }
    
def init_learning_table():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_learning_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vocab_id INTEGER,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def init_learning_progress_table():
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_learning_progress (
            vocab_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_result TEXT,
            last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

