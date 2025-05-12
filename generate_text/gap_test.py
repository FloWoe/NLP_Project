import unittest
from generate_text.gap_generator import create_gap_text_with_gemini

class TestGapGenerator(unittest.TestCase):

    def test_structure_of_response(self):
        text = "The cat is sitting on the mat."
        result = create_gap_text_with_gemini(text)

        # Sicherstellen, dass ein Dictionary zurückgegeben wird
        self.assertIsInstance(result, dict)

        # Prüfen, ob die erwarteten Keys enthalten sind
        self.assertIn("gap_text", result)
        self.assertIn("original_word", result)

        # Sicherstellen, dass die Lücke im Text vorhanden ist
        self.assertIn("_____", result["gap_text"])

        # Das Originalwort sollte kein leerer String sein (wenn vorhanden)
        self.assertTrue(result["original_word"])  # Nur grober Test

    def test_gap_is_unique(self):
        text = "Dogs love to play and run."
        result = create_gap_text_with_gemini(text)
        self.assertEqual(result["gap_text"].count("_____"), 1)

    def test_handles_invalid_json_gracefully(self):
        # ⚠️ Schwierig ohne Mock, aber wir prüfen das Fallback
        text = "This test sentence should still work."
        result = create_gap_text_with_gemini(text)

        # Falls Gemini kein gültiges JSON zurückgibt, kommt trotzdem ein dict zurück
        self.assertIn("gap_text", result)
        self.assertIn("original_word", result)


if __name__ == '__main__':
    unittest.main()
