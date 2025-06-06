import unittest
import sys
import os

# Pfad zum Hauptordner setzen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from word_finding import word_alignment


class TestWordAlignment(unittest.TestCase):

    def test_stem(self):
        self.assertEqual(word_alignment.stem("bäume", "de"), "baum")
        self.assertEqual(word_alignment.stem("running", "en"), "run")

    def test_lemmatize(self):
        lemma = word_alignment.lemmatize("gelaufen", "de", "Ich bin schnell gelaufen.")
        self.assertEqual(lemma, "laufen")

        lemma2 = word_alignment.lemmatize("running", "en", "He is running fast.")
        self.assertEqual(lemma2, "run")

    def test_get_pos_tag(self):
        pos = word_alignment.get_pos_tag("Hund", "de", "Der Hund bellt.")
        self.assertEqual(pos, "NOUN")

        pos2 = word_alignment.get_pos_tag("läuft", "de", "Er läuft schnell.")
        self.assertEqual(pos2, "VERB")

    def test_is_article_by_stem(self):
        self.assertTrue(word_alignment.is_article_by_stem("die", "de"))
        self.assertTrue(word_alignment.is_article_by_stem("the", "en"))
        self.assertFalse(word_alignment.is_article_by_stem("Haus", "de"))

    def test_is_verb_only(self):
        self.assertTrue(word_alignment.is_verb_only("läuft", "de"))
        self.assertTrue(word_alignment.is_verb_only("läuft ist", "de"))
        self.assertFalse(word_alignment.is_verb_only("der Hund läuft", "de"))

    def test_remove_articles(self):
        result = word_alignment.remove_articles("der große Hund", "de")
        self.assertEqual(result, "große Hund")

        result2 = word_alignment.remove_articles("the big dog", "en")
        self.assertEqual(result2, "big dog")

    def test_extract_lemmas_from_phrase(self):
        lemmas = word_alignment.extract_lemmas_from_phrase("Der Hund bellt laut", "de")
        self.assertIn("hund", lemmas)
        self.assertIn("bellen", lemmas)

        lemmas2 = word_alignment.extract_lemmas_from_phrase("The dogs are barking loudly", "en")
        self.assertIn("dog", lemmas2)
        self.assertIn("bark", lemmas2)


if __name__ == "__main__":
    unittest.main()
