import json
import re
import unittest
from medeasy.evidence import source_passages
from medeasy.explain import parse_explanation, ExplanationError


class EvidenceTests(unittest.TestCase):
    def payload(self, refs):
        claim = lambda text: {"text": text, "evidence": refs}
        return {"summary": claim("This letter explains your discharge."),
                "action_required": [claim("Pay £15.00 by 28 October 2026.")],
                "important_details": [claim("Reference: MED-0042")]}

    def test_ids_resolve_to_exact_original_text_with_line_breaks(self):
        source = "Discharge letter\nReference: MED-0042\nPay £15.00 by\n28 October 2026."
        passages = source_passages(source)
        result = parse_explanation(json.dumps(self.payload(["S0001"])), source, passages)
        self.assertEqual(result.actions[0].evidence, (source,))
        self.assertEqual(result.actions[0].text, "Pay £15.00 by 28 October 2026.")

    def test_unicode_spaces_are_preserved_in_retrieved_evidence(self):
        source = "Discharge letter\nReference: MED-0042\nPay £15.00\u00a0by\u202f28 October 2026."
        result = parse_explanation(json.dumps(self.payload(["S0001"])), source, source_passages(source))
        self.assertEqual(result.actions[0].evidence, (source,))

    def test_unknown_source_id_is_rejected(self):
        source = "Reference: MED-0042. Pay £15.00 by 28 October 2026."
        with self.assertRaisesRegex(ExplanationError, "EVIDENCE-ID"):
            parse_explanation(json.dumps(self.payload(["S9999"])), source, source_passages(source))

    def test_model_generated_quote_cannot_replace_id(self):
        source = "Reference: MED-0042. Pay £15.00 by 28 October 2026."
        with self.assertRaisesRegex(ExplanationError, "EVIDENCE-ID"):
            parse_explanation(json.dumps(self.payload([source])), source, source_passages(source))

    def test_invented_amount_still_rejected(self):
        source = "Reference: MED-0042. Pay £15.00 by 28 October 2026."
        payload = self.payload(["S0001"])
        payload["action_required"][0]["text"] = "Pay £99.00 by 28 October 2026."
        with self.assertRaisesRegex(ExplanationError, "number"):
            parse_explanation(json.dumps(payload), source, source_passages(source))

    def test_missing_value_can_still_have_no_evidence(self):
        source = "Reference: MED-0042. Pay £15.00 by 28 October 2026."
        payload = self.payload(["S0001"])
        payload["important_details"].append({"text": "Medicine dose: Not specified in the letter", "evidence": []})
        result = parse_explanation(json.dumps(payload), source, source_passages(source))
        self.assertEqual(result.details[-1].evidence, ())

    def test_passages_cover_text_in_order_without_cutting_tokens(self):
        source = ("Reference: MED-2026-0000042. Amount: £1,250.00.\n" * 100) + "Last detail."
        passages = source_passages(source)
        self.assertGreater(len(passages), 1)
        for quote in passages.values():
            self.assertIn(quote, source)
        normal = lambda text: re.sub(r"\s+", " ", text).strip()
        self.assertEqual(normal(" ".join(passages.values())), normal(source))
        self.assertEqual(sum(value.count("MED-2026-0000042") for value in passages.values()), 100)

    def test_oversized_token_is_kept_intact(self):
        source = "A" * 2000 + " end"
        passages = source_passages(source)
        self.assertEqual(passages["S0001"], "A" * 2000)
        self.assertEqual(passages["S0002"], "end")

    def test_multiple_supporting_passages_are_resolved_in_order(self):
        source = "Discharge letter\nReference: MED-0042\nPay £15.00 by 28 October 2026."
        passages = {"S0001": "Discharge letter\nReference: MED-0042", "S0002": "Pay £15.00 by 28 October 2026."}
        result = parse_explanation(json.dumps(self.payload(["S0001", "S0002"])), source, passages)
        self.assertEqual(result.actions[0].evidence, tuple(passages.values()))


if __name__ == "__main__":
    unittest.main()
