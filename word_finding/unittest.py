import unittest
from unittest.mock import patch
from word_finding.word_alignment import find_matching_word_crosslingual

class TestCrosslingualMatching(unittest.TestCase):

    @patch("word_finding.word_alignment.genai.GenerativeModel.generate_content")
    def test_dog_variants(self, mock_generate):
        mock_generate.return_value.text = "dog, dogs"
        result = find_matching_word_crosslingual(
            sentence_lang1="Der Hund liebt mich.",
            sentence_lang2="The dog loves me. Dogs love me.",
            selected_word="Hund",
            source_lang="de",
            target_lang="en"
        )
        self.assertIn("dog", result["translated_matches"])
        self.assertIn("dogs", result["translated_matches"])
        self.assertTrue(result["match_success"])

    @patch("word_finding.word_alignment.genai.GenerativeModel.generate_content")
    def test_feature_extraction_phrase(self, mock_generate):
        mock_generate.return_value.text = '"feature extraction"'
        result = find_matching_word_crosslingual(
            sentence_lang1="Die Merkmalsextraktion ist wichtig.",
            sentence_lang2="Feature extraction is important.",
            selected_word="Merkmalsextraktion",
            source_lang="de",
            target_lang="en"
        )
        self.assertIn("feature extraction", result["translated_matches"])
        self.assertTrue(result["match_success"])

    @patch("word_finding.word_alignment.genai.GenerativeModel.generate_content")
    def test_loves_love_variants(self, mock_generate):
        mock_generate.return_value.text = "love, loves"
        result = find_matching_word_crosslingual(
            sentence_lang1="Er liebt mich. Sie lieben mich.",
            sentence_lang2="He loves me. They love me.",
            selected_word="liebt",
            source_lang="de",
            target_lang="en"
        )
        self.assertIn("love", result["translated_matches"])
        self.assertIn("loves", result["translated_matches"])
        self.assertTrue(result["match_success"])

if __name__ == '__main__':
    unittest.main()
