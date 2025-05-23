import sqlite3
import random

# 🔧 Konfiguration
DAILY_GOAL = 5     # Tagesziel: 5 Vokabeln 2× richtig
SESSION_LIMIT = 5 # Max. Vokabeln pro Session

# 🧠 Session-Zwischenspeicher
session_stats = {
    "learned_words": {},        # {vocab_id: anzahl_als_known}
    "session_vocab_ids": set(), # aktive Vokabel-IDs in dieser Session
    "repeat_queue": []          # Queue für Wiederholungen (z. B. bei "nicht gewusst")
}

# 🔹 Hilfsfunktion: Hole Vokabel per ID
def fetch_vocab_by_id(vocab_id):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT original_word, translated_word
        FROM vocabulary
        WHERE id = ?
    """, (vocab_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": vocab_id,
            "original_word": row[0],
            "translated_word": row[1],
            "progress": get_session_progress()
        }
    return None

# 🔹 Hole nächste sinnvolle Vokabel (unter Berücksichtigung von Queue + Fortschritt)
def get_next_vocab():
    # 1. Wiederholungs-Queue prüfen
    while session_stats["repeat_queue"]:
        vocab_id = session_stats["repeat_queue"].pop(0)
        if session_stats["learned_words"].get(vocab_id, 0) < 2:
            return fetch_vocab_by_id(vocab_id)

    # 2. Nur Vokabeln nehmen, die noch nicht 2× gewusst wurden
    available_ids = [
        vid for vid in session_stats["session_vocab_ids"]
        if session_stats["learned_words"].get(vid, 0) < 2
    ]

    if not available_ids:
        return None  # Alle Vokabeln gelernt

    vocab_id = random.choice(available_ids)
    return fetch_vocab_by_id(vocab_id)

# 🔹 Lernfortschritt aktualisieren + Verlauf speichern
def update_learning_progress(vocab_id, result):
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()

    # Aktuelle Streak-Werte lesen
    cursor.execute("SELECT streak FROM vocab_learning_progress WHERE vocab_id = ?", (vocab_id,))
    row = cursor.fetchone()

    if row:
        current_streak = row[0]
        if result == "known":
            new_streak = current_streak + 1
        elif result == "partial":
            new_streak = max(1, current_streak - 1)
        else:
            new_streak = 0
    else:
        new_streak = 1 if result == "known" else 0

    # Tabelle aktualisieren oder anlegen
    cursor.execute("""
        INSERT INTO vocab_learning_progress (vocab_id, streak, last_result, last_reviewed)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(vocab_id) DO UPDATE SET
            streak = excluded.streak,
            last_result = excluded.last_result,
            last_reviewed = CURRENT_TIMESTAMP
    """, (vocab_id, new_streak, result))

    # Verlauf speichern
    cursor.execute("""
        INSERT INTO vocab_learning_results (vocab_id, result)
        VALUES (?, ?)
    """, (vocab_id, result))

    conn.commit()
    conn.close()

    # Session-Tracking aktualisieren
    if result == "known":
        session_stats["learned_words"][vocab_id] = session_stats["learned_words"].get(vocab_id, 0) + 1
    elif result == "partial":
        pass  # nichts tun
    else:  # unknown
        session_stats["learned_words"][vocab_id] = 0
        if vocab_id not in session_stats["repeat_queue"]:
            session_stats["repeat_queue"].append(vocab_id)

# 🔹 Tagesziel erreicht?
def check_daily_goal_achieved():
    count = sum(1 for c in session_stats["learned_words"].values() if c >= 2)
    return count >= DAILY_GOAL

# 🔹 Fortschrittsdaten für Balken etc.
def get_session_progress():
    correct = sum(1 for c in session_stats["learned_words"].values() if c >= 2)
    total = SESSION_LIMIT
    return {
        "correct": correct,
        "total": total,
        "percent": round((correct / total) * 100) if total > 0 else 0
    }

# 🔹 Neue Session vorbereiten (z. B. beim Klick auf "Session starten")
def start_new_session():
    session_stats["learned_words"].clear()
    session_stats["repeat_queue"].clear()
    session_stats["session_vocab_ids"].clear()

    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM vocabulary
        ORDER BY RANDOM()
        LIMIT ?
    """, (SESSION_LIMIT,))
    rows = cursor.fetchall()
    conn.close()

    session_stats["session_vocab_ids"] = set(row[0] for row in rows)

# 🔹 Reset manuell
def reset_session():
    session_stats["learned_words"].clear()
    session_stats["repeat_queue"].clear()
    session_stats["session_vocab_ids"].clear()
