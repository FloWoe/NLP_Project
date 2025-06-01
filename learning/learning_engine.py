# learning_engine.py

import sqlite3
import random
import os
from datetime import datetime, timedelta # Für Zeitstempel und SRS-Berechnungen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'Database', 'vocab.db')

# 🔧 Konfiguration (bleibt global, gilt pro User)
DAILY_GOAL_PER_USER = 5     # Tagesziel: 5 Vokabeln 2× richtig pro User
SESSION_LIMIT_PER_USER = 10 # Max. Vokabeln pro Session pro User (ggf. anpassen)
                            # War vorher 5, kann je nach Wunsch geändert werden.

# 🧠 Session-Zwischenspeicher (JETZT BENUTZERSPEZIFISCH)
# Struktur:
# user_sessions = {
#     user_id_1: {
#         "learned_words": {vocab_id: count_known_in_session}, # Wie oft in dieser Session als "known" markiert
#         "session_vocab_ids": set(),  # IDs der Vokabeln, die für diese Session ausgewählt wurden
#         "repeat_queue": [],          # Vokabeln, die in dieser Session falsch waren und wiederholt werden sollen
#         "active": False              # Flag, ob eine Session aktiv via /start-session gestartet wurde
#     },
#     user_id_2: { ... }
# }
user_sessions = {}

# --- Hilfsfunktionen für den Session-Cache ---

def _get_user_session(user_id: int) -> dict:
    """Holt oder initialisiert die Session-Daten für einen Benutzer."""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "learned_words": {},
            "session_vocab_ids": set(),
            "repeat_queue": [],
            "active": False
        }
    return user_sessions[user_id]

def _clear_user_session_data(user_id: int):
    """Setzt die Lerndaten einer Benutzersession zurück, behält aber den User-Eintrag."""
    session = _get_user_session(user_id) # Stellt sicher, dass der Key existiert
    session["learned_words"].clear()
    session["session_vocab_ids"].clear()
    session["repeat_queue"].clear()
    session["active"] = False


# --- Angepasste Lern-Engine Funktionen ---

# 🔹 Hilfsfunktion: Hole Vokabel per ID (benötigt user_id für DB und Session-Fortschritt)
def fetch_vocab_details_for_session(user_id: int, vocab_id: int) -> dict | None:
    """Holt Vokabeldetails und verknüpft sie mit dem aktuellen Session-Fortschritt des Users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Stellt sicher, dass die Vokabel auch dem User gehört
    cursor.execute("""
        SELECT original_word, translated_word, source_lang, target_lang, original_sentence, translated_sentence
        FROM vocabulary
        WHERE id = ? AND user_id = ?
    """, (vocab_id, user_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        session_progress_data = get_session_progress(user_id) # Holt den aktuellen Fortschritt DIESER Session
        return {
            "id": vocab_id,
            "original_word": row[0],
            "translated_word": row[1],
            "source_lang": row[2],
            "target_lang": row[3],
            "original_sentence": row[4],
            "translated_sentence": row[5],
            "progress": session_progress_data # Fügt den aktuellen Session-Fortschritt hinzu
        }
    return None

# 🔹 Hole nächste sinnvolle Vokabel (JETZT mit user_id)
def get_next_vocab(user_id: int) -> dict | None:
    session = _get_user_session(user_id)

    if not session["active"]:
        print(f"Info: User {user_id} hat keine aktive Lernsession. Bitte zuerst '/start-session' aufrufen.")
        return None
    if not session["session_vocab_ids"]:
        print(f"Info: Keine Vokabeln in der aktuellen Session für User {user_id}.")
        return None

    # 1. Wiederholungs-Queue prüfen (Vokabeln, die in dieser Session falsch waren)
    while session["repeat_queue"]:
        vocab_id_to_repeat = session["repeat_queue"].pop(0) # FIFO
        # Nur wiederholen, wenn sie in dieser Session noch nicht 2x richtig war
        if session["learned_words"].get(vocab_id_to_repeat, 0) < 2:
            print(f"User {user_id}: Wiederholung für Vocab ID {vocab_id_to_repeat} aus Queue.")
            return fetch_vocab_details_for_session(user_id, vocab_id_to_repeat)

    # 2. Neue/andere Vokabeln aus der Session nehmen, die noch nicht 2x gewusst wurden
    available_ids_for_learning = [
        vid for vid in session["session_vocab_ids"]
        if session["learned_words"].get(vid, 0) < 2
    ]

    if not available_ids_for_learning:
        print(f"Info: User {user_id} hat alle Vokabeln dieser Session ({len(session['session_vocab_ids'])}) gelernt.")
        return None  # Alle Vokabeln dieser Session gelernt

    # Zufällige Auswahl aus den noch zu lernenden Vokabeln der Session
    next_vocab_id = random.choice(available_ids_for_learning)
    print(f"User {user_id}: Nächste Vokabel ID {next_vocab_id} zum Lernen ausgewählt.")
    return fetch_vocab_details_for_session(user_id, next_vocab_id)

# 🔹 Lernfortschritt aktualisieren + Verlauf speichern (JETZT mit user_id)
def update_learning_progress(user_id: int, vocab_id: int, result_status: str):
    """
    Aktualisiert den Lernfortschritt in der DB und im Session-Cache.
    result_status: z.B. "known", "partial", "unknown"
    """
    session = _get_user_session(user_id)
    # Es ist okay, auch ohne aktive Session den DB-Fortschritt zu aktualisieren,
    # aber Session-Tracking macht nur Sinn, wenn eine Session aktiv ist.

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- SRS-Logik (vereinfacht, kann durch SM-2 etc. ersetzt werden) ---
    # 1. Aktuellen Lernstand aus der DB holen (vocab_learning_progress)
    cursor.execute("""
        SELECT streak, ease_factor, interval, next_review_due
        FROM vocab_learning_progress
        WHERE user_id = ? AND vocab_id = ?
    """, (user_id, vocab_id))
    progress_row = cursor.fetchone()

    current_streak = 0
    ease_factor = 2.5  # Standard-Ease-Factor
    interval_days = 0  # In Tagen

    if progress_row:
        current_streak = progress_row[0] if progress_row[0] is not None else 0
        ease_factor = progress_row[1] if progress_row[1] is not None else 2.5
        interval_days = progress_row[2] if progress_row[2] is not None else 0

    # 2. Neuen Lernstand basierend auf 'result_status' berechnen
    if result_status == "known":
        new_streak = current_streak + 1
        if interval_days == 0: # Erstes Mal richtig
            interval_days = 1
        elif interval_days == 1: # Zweites Mal richtig
            interval_days = 3 # oder 6 je nach SRS-Variante
        else:
            interval_days = round(interval_days * ease_factor)
        ease_factor = max(1.3, ease_factor + 0.1) # Leicht erhöhen, aber nicht zu niedrig
    elif result_status == "partial":
        new_streak = max(0, current_streak -1) # Streak reduzieren oder auf 0 setzen
        interval_days = max(1, round(interval_days * 0.8)) # Intervall verkürzen, aber min 1 Tag
        ease_factor = max(1.3, ease_factor - 0.1)  # Leicht senken
    else:  # "unknown"
        new_streak = 0
        interval_days = 0 # Sofort wiederholen / nächster Tag
        ease_factor = max(1.3, ease_factor - 0.2) # Stärker senken
        # Bei "unknown" die Vokabel in der aktuellen Session-Repeat-Queue priorisieren
        if session["active"] and vocab_id not in session["repeat_queue"]:
             session["repeat_queue"].insert(0, vocab_id) # An den Anfang der Queue für baldige Wiederholung

    # Mindestintervall von 1 Tag, außer bei "unknown" (0 Tage)
    if result_status != "unknown" and interval_days < 1:
        interval_days = 1
    
    # Begrenze das Intervall, um nicht zu weit in die Zukunft zu planen
    max_interval = 365 # z.B. ein Jahr
    interval_days = min(interval_days, max_interval)

    next_review_timestamp = datetime.now() + timedelta(days=interval_days)
    last_reviewed_timestamp = datetime.now()

    # 3. `vocab_learning_progress` in der DB aktualisieren oder neu anlegen
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
    """, (user_id, vocab_id, new_streak, result_status, last_reviewed_timestamp,
          next_review_timestamp, ease_factor, interval_days))

    # 4. Ergebnis in `vocab_learning_results` für den Verlauf speichern
    cursor.execute("""
        INSERT INTO vocab_learning_results (user_id, vocab_id, result, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, vocab_id, result_status, last_reviewed_timestamp))

    conn.commit()
    conn.close()

    print(f"User {user_id}: Lernfortschritt für Vocab ID {vocab_id} mit '{result_status}' gespeichert. Neuer Streak: {new_streak}, Nächste Prüfung: {next_review_timestamp.date()}")

    # 5. Session-Tracking für den aktuellen User aktualisieren (nur wenn Session aktiv)
    if session["active"]:
        if result_status == "known":
            session["learned_words"][vocab_id] = session["learned_words"].get(vocab_id, 0) + 1
        elif result_status == "partial":
            # Bei "partial" zählt es nicht als "learned" für das Tagesziel in dieser Session,
            # aber die Vokabel könnte in die repeat_queue kommen (siehe oben).
            pass
        else:  # "unknown"
            session["learned_words"][vocab_id] = 0 # Zähler für "known in session" zurücksetzen
            # Wurde bereits oben in die repeat_queue gepackt.

# 🔹 Tagesziel erreicht? (JETZT mit user_id)
def check_daily_goal_achieved(user_id: int) -> bool:
    session = _get_user_session(user_id)
    if not session["active"]:
        return False # Kein Tagesziel ohne aktive Session relevant

    # Zählt Vokabeln, die in dieser Session mindestens 2x als "known" markiert wurden
    count_fully_learned_in_session = sum(1 for count in session["learned_words"].values() if count >= 2)
    achieved = count_fully_learned_in_session >= DAILY_GOAL_PER_USER
    if achieved:
        print(f"User {user_id}: Tagesziel von {DAILY_GOAL_PER_USER} erreicht ({count_fully_learned_in_session} Vokabeln 2x 'known').")
    return achieved

# 🔹 Fortschrittsdaten für Balken etc. (JETZT mit user_id)
def get_session_progress(user_id: int) -> dict:
    session = _get_user_session(user_id)

    if not session["active"] or not session["session_vocab_ids"]:
        return {"correct": 0, "total": SESSION_LIMIT_PER_USER, "percent": 0, "active": False}

    # "Correct" zählt hier, wie viele Vokabeln der aktuellen Session 2x als "known" markiert wurden
    correct_in_session = sum(1 for vocab_id in session["session_vocab_ids"]
                             if session["learned_words"].get(vocab_id, 0) >= 2)

    total_in_session = len(session["session_vocab_ids"])

    return {
        "correct": correct_in_session,
        "total": total_in_session if total_in_session > 0 else SESSION_LIMIT_PER_USER, # Fallback
        "percent": round((correct_in_session / total_in_session) * 100) if total_in_session > 0 else 0,
        "active": session["active"]
    }

# 🔹 Neue Session vorbereiten (JETZT mit user_id)
def start_new_session(user_id: int):
    _clear_user_session_data(user_id) # Alte In-Memory Session-Daten für den User löschen
    session = _get_user_session(user_id) # Stellt sicher, dass der User-Eintrag existiert und initialisiert wird

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Wähle Vokabeln FÜR DIESEN BENUTZER aus.
    # Priorisiert Vokabeln, die laut `vocab_learning_progress` fällig sind.
    # Wenn nicht genug fällige da sind, fülle mit den am längsten nicht geübten oder neuen auf.
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        SELECT v.id
        FROM vocabulary v
        LEFT JOIN vocab_learning_progress vlp ON v.id = vlp.vocab_id AND vlp.user_id = ?
        WHERE v.user_id = ?
        ORDER BY
            CASE
                WHEN vlp.next_review_due IS NULL THEN 0 -- Neue Vokabeln (ganz oben)
                WHEN vlp.next_review_due <= ? THEN 1   -- Fällige Vokabeln
                ELSE 2                               -- Noch nicht fällige
            END,
            vlp.next_review_due ASC, -- Fällige nach Datum
            vlp.last_reviewed ASC,   -- Länger nicht geübte
            RANDOM()                 -- Zufällige Auswahl bei Gleichstand
        LIMIT ?
    """, (user_id, user_id, now_iso, SESSION_LIMIT_PER_USER))
    rows = cursor.fetchall()
    conn.close()

    session["session_vocab_ids"] = set(row[0] for row in rows)
    session["learned_words"].clear() # Sicherstellen, dass Zähler für neue Session leer ist
    session["repeat_queue"].clear()
    session["active"] = True # Session als aktiv markieren

    if not session["session_vocab_ids"]:
        print(f"User {user_id}: Keine Vokabeln für neue Session gefunden (DB leer oder alle gelernt?).")
    else:
        print(f"User {user_id}: Neue Lernsession gestartet mit {len(session['session_vocab_ids'])} Vokabeln: {list(session['session_vocab_ids'])}.")

# 🔹 Reset manuell (JETZT mit user_id)
def reset_session(user_id: int):
    _clear_user_session_data(user_id)
    print(f"User {user_id}: Lernsession-Cache wurde manuell zurückgesetzt.")