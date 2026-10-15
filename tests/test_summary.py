import json
import unittest
from medeasy.summary import split_summary
from medeasy.explain import parse_explanation, render_text, ExplanationError


class SummaryTests(unittest.TestCase):
    def test_titles_and_initials_do_not_break_summary(self):
        for text in ("This letter is from Dr. Jones about your care.",
                     "This letter is for Mr. A. Smith about his hospital stay.",
                     "This letter explains care, e.g. follow-up visits."):
            self.assertEqual(split_summary(text), (text, ""))

    def test_amounts_dates_and_abbreviations_preserved(self):
        text = "Dr. Jones wrote on 28. October 2026 about £15.00. Payment is due."
        self.assertEqual(split_summary(text), ("Dr. Jones wrote on 28. October 2026 about £15.00.", "Payment is due."))

    def test_lowercase_sentence_still_split(self):
        self.assertEqual(split_summary("This is a letter. it explains your care."),
                         ("This is a letter.", "it explains your care."))

    def test_quoted_sentence_preserves_punctuation(self):
        self.assertEqual(split_summary('The letter says "come back." Bring your notes.'),
                         ('The letter says "come back."', 'Bring your notes.'))

    def test_multiple_sentences_preserved_in_details_and_export(self):
        source = "This is a discharge letter. Visit on 21 October 2026. Pay £15.00."
        claim = lambda text: {"text": text, "evidence": [source]}
        payload = {"summary": claim(source), "action_required": [claim("Visit on 21 October 2026.")],
                   "important_details": [claim("Pay £15.00.")]}
        result = parse_explanation(json.dumps(payload), source)
        self.assertEqual(result.summary.text, "This is a discharge letter.")
        self.assertEqual(result.details[0].text, "Visit on 21 October 2026. Pay £15.00.")
        exported = render_text(result, source)
        self.assertEqual([line for line in exported.splitlines() if line[:2] in ("1.", "2.", "3.")],
                         ["1. SUMMARY", "2. ACTION REQUIRED", "3. IMPORTANT DETAILS"])
        self.assertIn("21 October 2026", exported)
        self.assertIn("£15.00", exported)

    def test_unsupported_overflow_still_rejected(self):
        source = "This is a discharge letter. Pay £15.00."
        claim = lambda text: {"text": text, "evidence": [source]}
        payload = {"summary": claim("This is a discharge letter. Pay £99.00."),
                   "action_required": [claim("Pay £15.00.")], "important_details": [claim("Pay £15.00.")]}
        with self.assertRaises(ExplanationError):
            parse_explanation(json.dumps(payload), source)


if __name__ == "__main__":
    unittest.main()
