import unittest
from generate_text.text_generator import generate_text_by_language

class TestTextGeneration(unittest.TestCase):

    def test_text_is_not_empty(self):
        text = generate_text_by_language("de", "medium")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 10)

    def test_text_changes_on_multiple_calls(self):
        # Zwei Texte generieren und vergleichen
        text1 = generate_text_by_language("en", "easy")
        text2 = generate_text_by_language("en", "easy")
        self.assertNotEqual(text1.strip(), text2.strip())

    def test_supported_difficulties(self):
        for difficulty in ["easy", "medium", "hard"]:
            text = generate_text_by_language("de", difficulty)
            self.assertIn(" ", text)  # sollte mindestens mehrere Wörter haben

    def test_fallback_to_medium_on_invalid_difficulty(self):
        text = generate_text_by_language("de", "invalid")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 10)


if __name__ == '__main__':
    unittest.main()
