# vocab_db.py

import sqlite3
from dataclasses import dataclass
from rapidfuzz import fuzz, process # Beibehalten, falls direkt hier genutzt, sonst entfernen
from rapidfuzz.distance import Levenshtein # Stellen sicher, dass es importiert ist, wenn search_vocab_advanced es nutzt
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime, timedelta # Für Lernfortschritt (next_review_due)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'Database', 'vocab.db')

# 🔹 Datenmodell VocabEntry
@dataclass
class VocabEntry:
    original_word: str
    translated_word: str
    source_lang: str
    target_lang: str
    original_sentence: str
    translated_sentence: str

# --- Initialisierungsfunktionen ---
def init_user_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def init_db(): # vocabulary table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_word TEXT,
            translated_word TEXT,
            source_lang TEXT,
            target_lang TEXT,
            original_sentence TEXT,
            translated_sentence TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """) # ON DELETE CASCADE für user_id hinzugefügt: Wenn User gelöscht, werden auch seine Vokabeln gelöscht.
    conn.commit()
    conn.close()

def init_result_table(): # quiz_results table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language TEXT,
            vocab_score INTEGER,
            sentence_score INTEGER,
            total_score INTEGER,
            passed BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """) # ON DELETE CASCADE für user_id
    conn.commit()
    conn.close()

def init_learning_table(): # vocab_learning_results table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_learning_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vocab_id INTEGER NOT NULL,
            result TEXT, -- e.g., 'correct', 'incorrect', 'easy', 'hard'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
        )
    """) # ON DELETE CASCADE für user_id
    conn.commit()
    conn.close()

def init_learning_progress_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_learning_progress (
            user_id INTEGER NOT NULL,
            vocab_id INTEGER NOT NULL,
            streak INTEGER DEFAULT 0,
            last_result TEXT,
            last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            next_review_due TIMESTAMP,
            ease_factor REAL DEFAULT 2.5, -- For SM-2 algorithm like SRS
            interval INTEGER DEFAULT 0,   -- Current interval in days for SRS
            PRIMARY KEY (user_id, vocab_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
        )
    """) # ON DELETE CASCADE für user_id
    conn.commit()
    conn.close()

# --- User Management Funktionen ---
def create_user(username, email, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError: # Username oder Email bereits vorhanden
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data # (id, username, email, password_hash)

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

# --- Vokabel Management Funktionen ---
def save_vocab(user_id: int, entry: VocabEntry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vocabulary (
            user_id, original_word, translated_word,
            source_lang, target_lang,
            original_sentence, translated_sentence
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, entry.original_word, entry.translated_word,
        entry.source_lang, entry.target_lang,
        entry.original_sentence, entry.translated_sentence
    ))
    conn.commit()
    conn.close()

def get_vocab_by_target_lang(user_id: int, lang_code: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence, created_at
        FROM vocabulary
        WHERE user_id = ? AND target_lang LIKE ?
        ORDER BY created_at DESC
    """, (user_id, f"{lang_code}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_vocab(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence, created_at
        FROM vocabulary
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_vocab_entry_by_id(user_id: int, vocab_id: int) -> VocabEntry | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence
        FROM vocabulary
        WHERE user_id = ? AND id = ?
    """, (user_id, vocab_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return VocabEntry(
            original_word=row[0],
            translated_word=row[1],
            source_lang=row[2],
            target_lang=row[3],
            original_sentence=row[4],
            translated_sentence=row[5]
        )
    return None


def get_random_vocab_entry(user_id: int) -> VocabEntry | None:
    all_user_vocab = get_all_vocab(user_id)
    if not all_user_vocab:
        return None
    # random.choice erwartet eine nicht-leere Sequenz
    chosen_row_tuple = random.choice(all_user_vocab)
    # Die Tupel-Indizes müssen zu deiner SELECT-Anweisung in get_all_vocab passen
    # (id[0], original_word[1], translated_word[2], source_lang[3], target_lang[4],
    #  original_sentence[5], translated_sentence[6], created_at[7])
    return VocabEntry(
        original_word=chosen_row_tuple[1],
        translated_word=chosen_row_tuple[2],
        source_lang=chosen_row_tuple[3],
        target_lang=chosen_row_tuple[4],
        original_sentence=chosen_row_tuple[5],
        translated_sentence=chosen_row_tuple[6]
    )

def search_vocab_advanced(user_id: int, query: str, top_k=15):
    query_lower = query.lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, original_sentence, translated_sentence
        FROM vocabulary
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row_tuple in rows: # row ist hier ein Tupel (id, original_word, ...)
        original_word = row_tuple[1].lower() if row_tuple[1] else ""
        translated_word = row_tuple[2].lower() if row_tuple[2] else ""

        lev_dist_orig = Levenshtein.distance(query_lower, original_word)
        lev_dist_trans = Levenshtein.distance(query_lower, translated_word)
        lev_dist = min(lev_dist_orig, lev_dist_trans)

        len_q = len(query_lower)
        len_ow = len(original_word)
        len_tw = len(translated_word)

        # Wähle die Länge des Wortes, das die geringste Distanz hatte, oder die Query-Länge
        # Dies ist eine mögliche Normalisierungsstrategie. Es gibt viele.
        # Hier verwenden wir die maximale Länge der verglichenen Strings, um zu normalisieren.
        # Eine andere Möglichkeit ist, die Länge des DB-Wortes zu nehmen, das näher dran war.
        relevant_len = len_ow if lev_dist_orig <= lev_dist_trans else len_tw
        max_len_for_norm = max(len_q, relevant_len)

        if max_len_for_norm == 0:
            similarity_score = 1.0 if lev_dist == 0 else 0.0 # Beide Strings leer und Query leer
        else:
            similarity_score = 1 - (lev_dist / max_len_for_norm)

        if similarity_score >= 0.6:
            results.append((similarity_score, row_tuple))

    best = sorted(results, key=lambda x: x[0], reverse=True)[:top_k]

    return [dict(
        id=r_tuple[1][0], # Das ist r_tuple[1] (das ist row_tuple) und dessen erstes Element (id)
        original_word=r_tuple[1][1],
        translated_word=r_tuple[1][2],
        original_sentence=r_tuple[1][3] if r_tuple[1][3] else "",
        translated_sentence=r_tuple[1][4] if r_tuple[1][4] else ""
    ) for r_tuple in best]


def get_vocab_for_quiz(user_id: int, limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_word, translated_word, source_lang, target_lang,
               original_sentence, translated_sentence
        FROM vocabulary
        WHERE user_id = ?
        ORDER BY RANDOM()
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_vocab_entry(user_id: int, vocab_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocabulary WHERE id = ? AND user_id = ?", (vocab_id, user_id))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()
    return deleted_rows > 0 # True if a row was deleted

def delete_all_user_vocab(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocabulary WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# --- Quiz Ergebnis Funktionen ---
def save_quiz_result(user_id: int, language: str, vocab_score: int, sentence_score: int, total_score: int, passed: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_results (
            user_id, language, vocab_score, sentence_score, total_score, passed
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, language, vocab_score, sentence_score, total_score, passed))
    conn.commit()
    conn.close()

def get_all_results(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, language, vocab_score, sentence_score, total_score, passed, timestamp
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_summary_stats(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ?", (user_id,))
    total_tests_tuple = cursor.fetchone()
    total_tests = total_tests_tuple[0] if total_tests_tuple else 0

    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE passed = 1 AND user_id = ?", (user_id,))
    passed_tests_tuple = cursor.fetchone()
    passed_tests = passed_tests_tuple[0] if passed_tests_tuple else 0

    conn.close()
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
    }

# --- Lernfortschritt Funktionen (Beispiele) ---
def record_learning_result(user_id: int, vocab_id: int, result: str):
    """Speichert ein einzelnes Lernergebnis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vocab_learning_results (user_id, vocab_id, result, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, vocab_id, result, datetime.now()))
    conn.commit()
    conn.close()

def update_learning_progress_entry(user_id: int, vocab_id: int, result: str, streak: int,
                                   next_review: datetime, ease: float, interval: int):
    """Aktualisiert oder fügt einen Eintrag in vocab_learning_progress hinzu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vocab_learning_progress
            (user_id, vocab_id, streak, last_result, last_reviewed, next_review_due, ease_factor, interval)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, vocab_id) DO UPDATE SET
            streak = excluded.streak,
            last_result = excluded.last_result,
            last_reviewed = excluded.last_reviewed,
            next_review_due = excluded.next_review_due,
            ease_factor = excluded.ease_factor,
            interval = excluded.interval
    """, (user_id, vocab_id, streak, result, datetime.now(), next_review, ease, interval))
    conn.commit()
    conn.close()

def get_learning_progress_entry(user_id: int, vocab_id: int):
    """Holt den Lernfortschritt für eine Vokabel."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT streak, last_result, last_reviewed, next_review_due, ease_factor, interval
        FROM vocab_learning_progress
        WHERE user_id = ? AND vocab_id = ?
    """, (user_id, vocab_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "streak": row[0], "last_result": row[1], "last_reviewed": row[2],
            "next_review_due": row[3], "ease_factor": row[4], "interval": row[5]
        }
    return None # Oder Standardwerte zurückgeben

def get_vocab_to_learn(user_id: int, limit: int = 10, due_now: bool = True):
    """
    Holt Vokabeln, die gelernt werden sollen.
    Priorisiert fällige Vokabeln, dann neue Vokabeln.
    Dies ist eine vereinfachte Logik.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    query = """
        SELECT v.id, v.original_word, v.translated_word, v.source_lang, v.target_lang,
               v.original_sentence, v.translated_sentence,
               lp.next_review_due, lp.streak
        FROM vocabulary v
        LEFT JOIN vocab_learning_progress lp ON v.id = lp.vocab_id AND lp.user_id = ?
        WHERE v.user_id = ?
    """
    params = [user_id, user_id]

    if due_now:
        query += " AND (lp.next_review_due IS NULL OR lp.next_review_due <= ?)"
        params.append(now_iso)

    query += " ORDER BY lp.next_review_due ASC, v.created_at ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_learning_activity_over_time(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(timestamp) AS date, COUNT(DISTINCT vocab_id)
        FROM vocab_learning_results
        WHERE user_id = ?
        GROUP BY date
        ORDER BY date
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {
        "labels": [row[0] for row in rows],
        "counts": [row[1] for row in rows]
    }

def get_language_levels(user_id: int):
    LEVELS = [("A1", 500), ("A2", 1000), ("B1", 2000), ("B2", 4000), ("C1", 8000), ("C2", 12000)]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_lang, COUNT(*)
        FROM vocabulary
        WHERE user_id = ?
        GROUP BY target_lang
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for lang, count in rows:
        level = "-"
        remaining = LEVELS[0][1]
        for i, (lvl, threshold) in enumerate(LEVELS):
            if count < threshold:
                level = "-" if i == 0 else LEVELS[i-1][0]
                remaining = threshold - count
                break
        else:
            level = LEVELS[-1][0]
            remaining = 0
        result.append({"language": lang, "level": level, "remaining": remaining})
    return result

# --- Hilfsfunktionen (falls benötigt) ---
# Zum Beispiel, um die Datenbank initial zu befüllen oder zu leeren für Tests
def clear_all_tables_for_user(user_id: int):
    """ACHTUNG: Löscht alle Daten dieses Benutzers aus den relevanten Tabellen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables_to_clear = ["vocabulary", "quiz_results", "vocab_learning_results", "vocab_learning_progress"]
    try:
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim Löschen der Tabellen für User {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_user_and_data(user_id: int):
    """Löscht einen Benutzer und alle seine zugehörigen Daten (dank ON DELETE CASCADE)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        # ON DELETE CASCADE sollte den Rest erledigen
    except sqlite3.Error as e:
        print(f"Fehler beim Löschen von User {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()