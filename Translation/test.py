import unittest
from Translation.translator import translate_text

class TestTranslateTextRealAPI(unittest.TestCase):

    def test_translate_german_to_english(self):
        result = translate_text("Guten Morgen", "en")
        self.assertIn("translated", result)
        self.assertTrue(len(result["translated"]) > 0)

    def test_translate_german_to_japanese_romaji(self):
        result = translate_text("Ich liebe dich", "ja")
        self.assertIn("translated", result)
        self.assertIn("reading", result)
        self.assertNotIn("愛", result["translated"])  # sollte Rōmaji sein
        self.assertTrue(result["translated"].replace(" ", "").isalpha())

    def test_invalid_language_code(self):
        with self.assertRaises(Exception) as context:
            translate_text("Hallo Welt", "xyz")  # ungültiger Sprachcode
        self.assertIn("Fehler bei der Übersetzung", str(context.exception))

if __name__ == "__main__":
    unittest.main()


