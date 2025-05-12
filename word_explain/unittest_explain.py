import unittest
from word_explain.Explain import explain_word

class TestExplainWord(unittest.TestCase):

    def test_explanation_contains_all_sections(self):
        text = "I saw many birds flying across the sky."
        word = "flying"
        html = explain_word(text, word)

        self.assertIsInstance(html, str)
        self.assertIn("<strong>Bedeutung", html)
        self.assertIn("<strong>Herkunft", html)
        self.assertIn("<strong>Grammatik", html)
        self.assertIn("<strong>Beispiel", html)
        self.assertIn("<p>", html)

    def test_no_markdown_or_codeblocks(self):
        text = "They are building a new school."
        word = "building"
        html = explain_word(text, word)

        self.assertNotIn("```", html)
        self.assertNotIn("**", html)
        self.assertNotIn("```html", html)

    def test_html_output_is_not_empty(self):
        html = explain_word("He played very well.", "played")
        self.assertTrue(len(html.strip()) > 0)

if __name__ == "__main__":
    unittest.main()
