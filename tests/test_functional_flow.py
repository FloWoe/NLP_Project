import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from vocab_storage import vocab_db
from vocab_storage.vocab_db import VocabEntry


class TestVocabStorageFlow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        vocab_db.init_user_table()
        vocab_db.init_db()
        vocab_db.init_result_table()
        vocab_db.init_learning_table()
        vocab_db.init_learning_progress_table()

        cls.username = "testuser"
        cls.email = "test@example.com"
        cls.password = "secure123"
        cls.user_id = vocab_db.create_user(cls.username, cls.email, cls.password)
        if cls.user_id is None:
            existing_user = vocab_db.get_user_by_username(cls.username)
            cls.user_id = existing_user[0]

    def setUp(self):
        vocab_db.clear_all_tables_for_user(self.user_id)

    def test_create_and_fetch_user(self):
        user = vocab_db.get_user_by_username(self.username)
        self.assertIsNotNone(user)
        self.assertEqual(user[1], self.username)
        self.assertEqual(user[2], self.email)

    def test_save_and_read_vocab_entry(self):
        entry = VocabEntry(
            original_word="apple",
            translated_word="Apfel",
            source_lang="en",
            target_lang="de",
            original_sentence="I like apples.",
            translated_sentence="Ich mag Äpfel."
        )
        vocab_db.save_vocab(self.user_id, entry)
        all_vocab = vocab_db.get_all_vocab(self.user_id)
        self.assertEqual(len(all_vocab), 1)

        db_entry = all_vocab[0]
        self.assertEqual(db_entry[1], "apple")
        self.assertEqual(db_entry[2], "Apfel")

    def test_get_vocab_entry_by_id(self):
        entry = VocabEntry(
            original_word="sun",
            translated_word="Sonne",
            source_lang="en",
            target_lang="de",
            original_sentence="The sun is shining.",
            translated_sentence="Die Sonne scheint."
        )
        vocab_db.save_vocab(self.user_id, entry)
        vocab_list = vocab_db.get_all_vocab(self.user_id)
        vocab_id = vocab_list[0][0]

        fetched_entry = vocab_db.get_vocab_entry_by_id(self.user_id, vocab_id)
        self.assertIsNotNone(fetched_entry)
        self.assertEqual(fetched_entry.original_word, "sun")
        self.assertEqual(fetched_entry.translated_word, "Sonne")

    def test_delete_vocab_entry(self):
        entry = VocabEntry(
            original_word="moon",
            translated_word="Mond",
            source_lang="en",
            target_lang="de",
            original_sentence="The moon is bright.",
            translated_sentence="Der Mond ist hell."
        )
        vocab_db.save_vocab(self.user_id, entry)
        vocab_list = vocab_db.get_all_vocab(self.user_id)
        vocab_id = vocab_list[0][0]

        deleted = vocab_db.delete_vocab_entry(self.user_id, vocab_id)
        self.assertTrue(deleted)
        self.assertEqual(len(vocab_db.get_all_vocab(self.user_id)), 0)

    def test_get_random_vocab_entry(self):
        entry = VocabEntry(
            original_word="tree",
            translated_word="Baum",
            source_lang="en",
            target_lang="de",
            original_sentence="The tree is tall.",
            translated_sentence="Der Baum ist hoch."
        )
        vocab_db.save_vocab(self.user_id, entry)
        random_entry = vocab_db.get_random_vocab_entry(self.user_id)
        self.assertIsNotNone(random_entry)
        self.assertEqual(random_entry.original_word, "tree")

    def test_search_vocab_advanced(self):
        entry = VocabEntry(
            original_word="information",
            translated_word="Information",
            source_lang="en",
            target_lang="de",
            original_sentence="Information is power.",
            translated_sentence="Information ist Macht."
        )
        vocab_db.save_vocab(self.user_id, entry)
        results = vocab_db.search_vocab_advanced(self.user_id, "informtion")  # absichtlich falsch
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['original_word'], "information")

    def test_lemmatization_on_save(self):
        entry = VocabEntry(
            original_word="running",
            translated_word="Laufen",
            source_lang="en",
            target_lang="de",
            original_sentence="He is running fast.",
            translated_sentence="Er läuft schnell."
        )
        vocab_db.save_vocab(self.user_id, entry)
        all_vocab = vocab_db.get_all_vocab(self.user_id)
        self.assertEqual(all_vocab[0][1], "run")  # Lemma von running ist run

    def test_delete_user_and_data(self):
        self.assertIsNotNone(vocab_db.get_user_by_id(self.user_id))
        vocab_db.delete_user_and_data(self.user_id)
        self.assertIsNone(vocab_db.get_user_by_id(self.user_id))
        self.__class__.user_id = vocab_db.create_user(self.username, self.email, self.password)

    @classmethod
    def tearDownClass(cls):
        vocab_db.delete_user_and_data(cls.user_id)


if __name__ == "__main__":
    unittest.main()

