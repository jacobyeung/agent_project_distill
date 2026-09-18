import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from student_pilot import conversion, conversion_v2 as v2
from student_pilot.common import canonical_bytes, digest_json, load_json


FIXTURE = Path(__file__).parent / "fixtures/conversion_3919.json"


def synthetic_payload(text=None):
    text = text or "The observation concerns the box. The box is visible in frame 1. The sequence starts with the box. This supports the stated answer."
    return {
        "question": "Describe the synthetic observation.", "options": [],
        "native_final_provenance": "<ANSWER>fixture</ANSWER>", "frame_metadata": {},
        "evidence": [{"id": "e0000", "kind": "archived_tool_result", "text": text,
                      "source_pointer": "/trace/1/content", "text_sha256": hashlib.sha256(text.encode()).hexdigest()}],
    }


def synthetic_document():
    sentences = ["The observation concerns the box.", "The box is visible in frame 1.",
                 "The sequence starts with the box.", "This supports the stated answer."]
    return {"status": "converted", "answer": "fixture", "explanation": [
        {"purpose": purpose, "claims": [{"text": text, "citations": [{"evidence_id": "e0000", "quote": text}]}]}
        for purpose, text in zip(("setup", "observations", "derivation", "conclusion"), sentences)
    ]}


class SpanResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE)
        cls.payload = cls.fixture["payload"]

    def test_real_3919_five_quotes_resolve_to_reviewed_offsets(self):
        citations = [citation for claim in self.fixture["provider_document"]["claims"] for citation in claim["citations"]]
        resolved = [v2.resolve_citation({key: citation[key] for key in ("evidence_id", "quote")}, self.payload) for citation in citations]
        self.assertEqual([[item["start"], item["end"]] for item in resolved], self.fixture["reviewed_offsets"])
        self.assertTrue(all(item["match_method"] == "exact" for item in resolved))
        evidence = {item["id"]: item for item in self.payload["evidence"]}
        for item in resolved:
            self.assertEqual(item["quote"], evidence[item["evidence_id"]]["text"][item["start"]:item["end"]])

    def test_ambiguous_and_overlapping_quotes_require_one_based_occurrence(self):
        payload = synthetic_payload("ababa")
        citation = {"evidence_id": "e0000", "quote": "aba"}
        with self.assertRaisesRegex(ValueError, "citation_ambiguous"):
            v2.resolve_citation(citation, payload)
        resolved = v2.resolve_citation({**citation, "occurrence": 2}, payload)
        self.assertEqual((resolved["start"], resolved["end"], resolved["match_count"]), (2, 5, 2))
        for occurrence in (0, -1, 3, True, "1"):
            with self.subTest(occurrence=occurrence), self.assertRaises(ValueError):
                v2.resolve_citation({**citation, "occurrence": occurrence}, payload)

    def test_missing_empty_and_unknown_evidence_are_rejected(self):
        for citation in ({"evidence_id": "e0000", "quote": "invented"},
                         {"evidence_id": "e0000", "quote": " \t"},
                         {"evidence_id": "native-final", "quote": "fixture"}):
            with self.subTest(citation=citation), self.assertRaises(ValueError):
                v2.resolve_citation(citation, synthetic_payload())

    def test_model_offsets_are_not_accepted_in_v2(self):
        with self.assertRaisesRegex(ValueError, "citation_schema"):
            v2.resolve_citation({"evidence_id": "e0000", "quote": "box", "start": 0, "end": 3}, synthetic_payload())

    def test_whitespace_normalization_maps_back_to_original_characters(self):
        payload = synthetic_payload("prefix chair:\t frame\n\u00a01 suffix")
        result = v2.resolve_citation({"evidence_id": "e0000", "quote": "chair: frame 1"}, payload)
        self.assertEqual(result["match_method"], "whitespace_normalized")
        self.assertEqual(result["quote"], "chair:\t frame\n\u00a01")
        self.assertEqual((result["start"], result["end"]), (7, 23))

    def test_nfc_normalization_maps_combining_characters_and_hangul(self):
        for source, quote in (("prefix cafe\u0301 suffix", "caf\u00e9"), ("x \u1100\u1161\u11a8 y", "\uac01"),
                              ("x cafe\u0301\t label y", "caf\u00e9 label")):
            with self.subTest(source=source):
                payload = synthetic_payload(source)
                result = v2.resolve_citation({"evidence_id": "e0000", "quote": quote}, payload)
                self.assertEqual(result["match_method"], "unicode_nfc")
                self.assertEqual(result["quote"], source[result["start"]:result["end"]])
                self.assertEqual(result["submitted_quote"], quote)

    def test_ambiguity_is_checked_after_normalization(self):
        payload = synthetic_payload("cafe\u0301 here cafe\u0301")
        with self.assertRaisesRegex(ValueError, "citation_ambiguous"):
            v2.resolve_citation({"evidence_id": "e0000", "quote": "caf\u00e9"}, payload)

    def test_exact_search_precedes_normalized_search(self):
        payload = synthetic_payload("box\t here; box here")
        result = v2.resolve_citation({"evidence_id": "e0000", "quote": "box here"}, payload)
        self.assertEqual(result["match_method"], "exact")
        self.assertEqual(result["start"], 11)


class GroundedContractTests(unittest.TestCase):
    def validate(self, document=None, payload=None):
        return conversion.validate_document(document or synthetic_document(), payload or synthetic_payload(), converter_version="v2")

    def test_claim_ids_are_assigned_in_paragraph_reading_order(self):
        document = synthetic_document()
        original = copy.deepcopy(document)
        result = self.validate(document)
        self.assertEqual([claim["id"] for claim in result["claims"]], ["c1", "c2", "c3", "c4"])
        self.assertEqual([item["source_pointer"] for item in result["claim_id_mapping"]],
                         [f"/explanation/{index}/claims/0" for index in range(4)])
        self.assertEqual(document, original)
        self.assertEqual(result["converter_version"], "v2")
        self.assertFalse(result["training_eligible"])
        self.assertFalse(result["semantic_grounding_verified"])

    def test_schema_does_not_ask_for_claim_ids_or_offsets(self):
        schema = v2.RESPONSE_SCHEMA
        paragraph = schema["properties"]["explanation"]["items"]
        claim = paragraph["properties"]["claims"]["items"]
        self.assertNotIn("id", claim["properties"])
        citation = claim["properties"]["citations"]["items"]
        self.assertEqual(set(citation["required"]), {"evidence_id", "quote"})
        self.assertEqual(set(citation["properties"]), {"evidence_id", "quote", "occurrence"})

    def test_schema_json_round_trip_and_paragraph_rendering(self):
        document = json.loads(json.dumps(synthetic_document()))
        schema = json.loads(json.dumps(v2.RESPONSE_SCHEMA))
        self.assertEqual(schema, v2.RESPONSE_SCHEMA)
        result = self.validate(document)
        expected = "\n\n".join(paragraph["claims"][0]["text"] for paragraph in document["explanation"])
        self.assertEqual(result["target"], expected + "\n\n<answer>fixture</answer>")
        self.assertEqual(result["target_sha256"], hashlib.sha256(result["target"].encode()).hexdigest())

    def test_thin_or_uncited_explanations_are_rejected(self):
        document = synthetic_document()
        document["explanation"] = document["explanation"][:2]
        with self.assertRaisesRegex(ValueError, "detailed_explanation_required"):
            self.validate(document)
        for field, value in (("text", "Uncited prose."), ("id", "claim_1")):
            document = synthetic_document()
            document["explanation"][0][field] = value
            with self.assertRaises(ValueError):
                self.validate(document)

    def test_bare_native_answer_requires_byte_exact_body(self):
        self.validate()
        for answer in ("<ANSWER>fixture</ANSWER>", " fixture", "fixture ", "Fixture", "fixture\n"):
            document = synthetic_document()
            document["answer"] = answer
            with self.subTest(answer=answer), self.assertRaisesRegex(ValueError, "agree verbatim"):
                self.validate(document)
        payload = synthetic_payload()
        payload["native_final_provenance"] = "<ANSWER> fixture </ANSWER>"
        document = synthetic_document()
        document["answer"] = " fixture "
        self.validate(document, payload)

    def test_tool_reference_in_target_not_in_private_citation(self):
        for text in ("the planner called find_frames_with_object", "The tool returned a result.",
                     "SAM3 finds the box.", "The Python code computes it.", "predict_2d_points locates it."):
            document = synthetic_document()
            document["explanation"][0]["claims"][0]["text"] = text
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "tool_reference_in_target"):
                self.validate(document)
        payload = synthetic_payload(synthetic_payload()["evidence"][0]["text"] + " The tool observed a box.")
        document = synthetic_document()
        document["explanation"][0]["claims"][0]["citations"].append({"evidence_id": "e0000", "quote": "The tool observed a box."})
        self.validate(document, payload)

    def test_tool_names_extracted_from_evidence_are_not_allowed_in_target(self):
        payload = synthetic_payload(synthetic_payload()["evidence"][0]["text"] + " `custom_detector` returned it.")
        document = synthetic_document()
        document["explanation"][0]["claims"][0]["text"] = "custom_detector returned it."
        with self.assertRaisesRegex(ValueError, "tool_reference_in_target"):
            self.validate(document, payload)

    def test_no_new_numeric_literals_or_native_final_only_evidence(self):
        document = synthetic_document()
        document["explanation"][1]["claims"][0]["text"] = "The box is visible in frame 999."
        with self.assertRaisesRegex(ValueError, "numeric"):
            self.validate(document)
        payload = synthetic_payload()
        payload["evidence"][0]["kind"] = "source_option"
        with self.assertRaisesRegex(ValueError, "Question/options"):
            self.validate(payload=payload)

    def test_sentence_final_source_numbers_support_nonfinal_target_numbers(self):
        document = synthetic_document()
        document["explanation"][1]["claims"][0]["text"] = "The box in frame 1 is visible."
        self.validate(document)

    def test_insufficient_evidence_stays_rejected(self):
        with self.assertRaises(ValueError):
            self.validate({"status": "insufficient_evidence", "answer": "", "explanation": []})

    def test_unknown_versions_fail_closed(self):
        with self.assertRaises(ValueError):
            conversion.make_request(synthetic_payload(), converter_version="v3")
        with self.assertRaises(ValueError):
            conversion.validate_document(synthetic_document(), synthetic_payload(), converter_version="v3")


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = load_json(FIXTURE)["payload"]
        cls.evidence = {item["id"]: item for item in cls.payload["evidence"]}

    def claim(self, text, evidence_id, quote):
        return {"id": "c1", "text": text, "citations": [v2.resolve_citation({"evidence_id": evidence_id, "quote": quote}, self.payload)]}

    def test_3919_keyboard_conflict_omission_names_evidence_pointer(self):
        text = "chair appears first at frame 1, then bookshelf at frame 10, door at frame 12, and then keyboard at frame 24."
        claim = self.claim(text, "e0039", text)
        with self.assertRaises(v2.GroundingError) as caught:
            v2.check_qualifications([claim], self.payload)
        self.assertEqual(caught.exception.reason, "qualification_omitted")
        self.assertEqual(caught.exception.details["evidence_id"], "e0039")
        self.assertEqual(caught.exception.details["source_pointer"], "/trace/104/content/0/thinking")

    def test_3919_keyboard_conflict_passes_when_qualified_and_cited(self):
        quote = "There's a discrepancy with the keyboard: it seems `find_frames_with_object` might be throwing a false positive at frame 1."
        text = "There is a discrepancy with the keyboard: its detection at frame 1 might be a false positive."
        claim = self.claim(text, "e0039", quote)
        v2.check_qualifications([claim], self.payload)
        v2.check_tool_references([claim], self.payload)

    def test_approximate_door_statement_must_stay_approximate(self):
        quote = "Based on the observed video sequence, it's making its first appearance around frame 12 or 13."
        for text, valid in (("The door appears in frame 12.", False), ("The door first appears around frame 12 or 13.", True)):
            claim = self.claim(text, "e0035", quote)
            if valid:
                v2.check_qualifications([claim], self.payload)
            else:
                with self.assertRaisesRegex(ValueError, "qualification_omitted"):
                    v2.check_qualifications([claim], self.payload)

    def test_qualification_word_without_qualified_citation_does_not_pass(self):
        quote = "The bookshelf comes in around frame 10."
        claim = self.claim("The bookshelf comes in around frame 10, with an assumption and a possible false positive.", "e0037", quote)
        with self.assertRaisesRegex(ValueError, "qualification_omitted"):
            v2.check_qualifications([claim], self.payload)

    def test_qualification_in_uncited_evidence_cannot_satisfy_another_entry(self):
        first = self.claim("The door is visible.", "e0035", "Based on the observed video sequence, it's making its first appearance around frame 12 or 13.")
        second = self.claim("The bookshelf comes in around frame 10.", "e0037", "The bookshelf comes in around frame 10.")
        with self.assertRaisesRegex(ValueError, "qualification_omitted"):
            v2.check_qualifications([first, second], self.payload)

    def test_assumptions_and_corrections_are_separate_requirements(self):
        for source, family in (("Assume the observation holds.", "assumption"), ("The previous identification was clearly wrong.", "correction")):
            payload = synthetic_payload(source)
            citation = v2.resolve_citation({"evidence_id": "e0000", "quote": source}, payload)
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, "qualification_omitted"):
                v2.check_qualifications([{"id": "c1", "text": "The identification holds.", "citations": [citation]}], payload)
            v2.check_qualifications([{"id": "c1", "text": source, "citations": [citation]}], payload)


class VersionAndBoundaryTests(unittest.TestCase):
    def test_v1_request_preserves_archived_payload_with_repaired_envelope_contract(self):
        fixture = load_json(FIXTURE)
        request = conversion.make_request(fixture["payload"], converter_version="v1")
        self.assertEqual(request["converter_version"], "v1")
        provider_request = {key: request[key] for key in ("model", "config", "contents")}
        self.assertEqual(json.loads(provider_request["contents"][0]["parts"][0]["text"]), fixture["payload"])
        self.assertIn("bare answer body", request["config"]["system_instruction"])
        self.assertEqual(request["config"]["response_json_schema"], conversion.RESPONSE_SCHEMA)

    def test_v1_still_rejects_original_3919_document(self):
        fixture = load_json(FIXTURE)
        with self.assertRaisesRegex(ValueError, "Claim"):
            conversion.validate_document(fixture["provider_document"], fixture["payload"], converter_version="v1")

    def test_v2_requests_pin_version_settings_and_evidence_kinds(self):
        request = conversion.make_request(synthetic_payload(), converter_version="v2")
        payload = json.loads(request["contents"][0]["parts"][0]["text"])
        self.assertEqual(request["converter_version"], "v2")
        self.assertEqual(payload["conversion_contract"]["version"], "v2")
        self.assertEqual(payload["evidence"][0]["kind"], "archived_tool_result")
        self.assertEqual(payload["evidence"][0]["evidence_role"], "tool_observation")
        self.assertEqual(request["model"], "gemini-3.1-pro-preview")
        for key, value in conversion.SETTINGS.items():
            self.assertEqual(request["config"][key], value)
        self.assertIn("bare", request["config"]["system_instruction"])

    def test_request_boundary_rejects_labels_scores_and_correctness_at_any_depth(self):
        for key in ("label", "labels", "gold_label", "ground_truth", "score", "is_correct", "correctness", "offline_grade"):
            for location in ("root", "evidence", "frame_metadata"):
                payload = synthetic_payload()
                container = payload if location == "root" else payload[location][0] if location == "evidence" else payload[location]
                container[key] = "DO_NOT_SEND"
                with self.subTest(key=key, location=location), self.assertRaisesRegex(ValueError, "request_boundary"):
                    conversion.make_request(payload, converter_version="v2")

    def test_every_decision_records_version_and_structured_rejection(self):
        payload = synthetic_payload()
        document = synthetic_document()
        document["explanation"][0]["claims"][0]["text"] = "the planner called find_frames_with_object"
        request = conversion.make_request(payload, converter_version="v2")
        context = {"row": {"qid": "fixture", "sources": {}}, "payload": payload,
                   "request": request, "request_sha256": digest_json(request), "converter_version": "v2"}
        response = {"status": "ok", "finish_reason": "STOP", "provider_served_model": conversion.MODEL,
                    "raw_response": [{"fixture": True}], "usage": {"prompt_token_count": 1, "candidates_token_count": 1, "total_token_count": 2},
                    "content": json.dumps(document)}
        saved = {}
        with patch.object(conversion, "repo_output", side_effect=Path), patch.object(conversion, "write_once", side_effect=lambda path, value: saved.update({Path(path).name: value})), patch.object(conversion, "binding", return_value={"fixture": True}), patch.object(conversion, "native_transport", return_value=response):
            decision = conversion.collect_one(context, Path("fixture-only"))
        self.assertEqual(decision["converter_version"], "v2")
        self.assertEqual(decision["reason"], "tool_reference_in_target")
        self.assertEqual(saved["provider.json"], response)
        self.assertNotIn("candidate.json", saved)
        self.assertFalse(decision["training_eligible"])


if __name__ == "__main__":
    unittest.main()
