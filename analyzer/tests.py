from django.test import TestCase
from django.urls import reverse

from .nlp.grammar import check_grammar, tokenize_sentences, tokenize_words
from .nlp.spelling import check_spelling, minimum_edit_distance


class EditDistanceTests(TestCase):
    def test_classic_levenshtein_examples(self):
        self.assertEqual(minimum_edit_distance("kitten", "sitting"), 3)
        self.assertEqual(minimum_edit_distance("book", "back"), 2)
        self.assertEqual(minimum_edit_distance("same", "same"), 0)


class SpellingTests(TestCase):
    def test_detects_and_corrects_simple_typo(self):
        issues, corrected = check_spelling("The quik brown fox.")
        self.assertEqual(issues[0]["word"], "quik")
        self.assertEqual(issues[0]["suggestion"], "quick")
        self.assertEqual(corrected, "The quick brown fox.")


class GrammarTests(TestCase):
    def test_agreement_article_and_tense_rules(self):
        issues = check_grammar("She are a apple. Yesterday I walk.")
        suggestions = {issue["suggestion"] for issue in issues}
        self.assertIn("is", suggestions)
        self.assertIn("an", suggestions)
        self.assertIn("walked", suggestions)

    def test_tokenizers(self):
        self.assertEqual(tokenize_sentences("One. Two!"), ["One.", "Two!"])
        self.assertEqual(tokenize_words("Hello, world!"), ["Hello", ",", "world", "!"])

    def test_past_tense_and_conventional_word_choice(self):
        issues = check_grammar("Yesterday I decide. Yesterday I break a toy. I make photographs.")
        suggestions = {issue["suggestion"] for issue in issues}
        self.assertIn("decided", suggestions)
        self.assertIn("broke", suggestions)
        self.assertIn("take", suggestions)


class WebFlowTests(TestCase):
    def test_home_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_analysis_is_saved_and_returned(self):
        response = self.client.post(reverse("analyze"), {"text": "She are a apple."}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("is", payload["corrected_text"])
        self.assertGreater(payload["issue_count"], 0)
        self.assertEqual(self.client.get(reverse("history_detail", args=[payload["analysis_id"]])).status_code, 200)

    def test_empty_text_is_rejected(self):
        response = self.client.post(reverse("analyze"), {"text": "   "}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)
