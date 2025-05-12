import unittest
from word_finding.word_alignment import find_matching_word_crosslingual


class TestWordAlignment(unittest.TestCase):

    def test_de_to_en_verbs(self):
        sentence_de = "Wir spielen draußen. Gestern spielten wir lange. Ich habe auch Fußball gespielt."
        sentence_en = "We play outside. Yesterday we played for a long time. I also played football."
        selected_word = "spielen"
        result = find_matching_word_crosslingual(
            sentence_lang1=sentence_de,
            sentence_lang2=sentence_en,
            selected_word=selected_word,
            source_lang="de",
            target_lang="en"
        )

        self.assertIn("played", result["translated_matches"])
        self.assertIn("spielen", result["original_matches"])
        self.assertIn("gespielt", result["original_matches"])
        self.assertTrue(len(result["translated_matches"]) > 0)

    def test_en_to_de_verbs(self):
        sentence_de = "Ich laufe jeden Morgen. Gestern lief ich fünf Kilometer. Ich bin viel gelaufen."
        sentence_en = "I run every morning. Yesterday I ran five kilometers. I have run a lot."
        selected_word = "ran"
        result = find_matching_word_crosslingual(
            sentence_lang1=sentence_en,
            sentence_lang2=sentence_de,
            selected_word=selected_word,
            source_lang="en",
            target_lang="de"
        )

        self.assertIn("lief", result["translated_matches"])
        self.assertIn("gelaufen", result["translated_matches"])
        self.assertIn("ran", result["original_matches"])
        self.assertIn("run", result["original_matches"])

    def test_de_to_en_nouns(self):
        sentence_de = "Die Hunde spielen im Garten. Ein Hund schläft."
        sentence_en = "The dogs are playing in the garden. One dog is sleeping."
        selected_word = "Hunde"
        result = find_matching_word_crosslingual(
            sentence_lang1=sentence_de,
            sentence_lang2=sentence_en,
            selected_word=selected_word,
            source_lang="de",
            target_lang="en"
        )

        self.assertIn("dogs", result["translated_matches"])
        self.assertIn("dog", result["translated_matches"])
        self.assertIn("Hunde", result["original_matches"])
        self.assertIn("Hund", result["original_matches"])

if __name__ == "__main__":
    unittest.main()
