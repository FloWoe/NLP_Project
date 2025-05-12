import sqlite3
from dataclasses import dataclass

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

