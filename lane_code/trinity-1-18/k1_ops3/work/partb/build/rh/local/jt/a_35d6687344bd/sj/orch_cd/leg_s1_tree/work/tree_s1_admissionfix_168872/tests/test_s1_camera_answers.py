import unittest

from evalpath.run import score_item


CASES = {
    "camera_displacement": "1.20",
    "camera_movement_direction": "B",
    "camera_obj_abs_dist": "0.98",
    "camera_rotation": "-99",
}


class CameraAnswerTests(unittest.TestCase):
    def score(self, kind, answer, text):
        task = dict(question_type=kind, ground_truth=answer,
                    answer_type="multiple_choice" if kind == "camera_movement_direction" else "numeric")
        return score_item(task, dict(text=text, finish="eos"))

    def test_plain_and_tagged_camera_answers_use_only_the_visible_suffix(self):
        for kind, answer in CASES.items():
            for tagged in (False, True):
                with self.subTest(kind=kind, tagged=tagged):
                    suffix = f"<answer>{answer}</answer>" if tagged else answer
                    raw = "<think>\n<answer>A</answer>\nA rejected number is 123.\n</think>\n\n"+suffix
                    result = self.score(kind, answer, raw)
                    self.assertEqual(result["response_text"], answer)
                    self.assertEqual(result["extract_branch"], "tag" if tagged else "final_line")
                    self.assertFalse(result["parse_failed"])
                    self.assertEqual(result["score"], 1)

    def test_unclosed_thinking_cannot_supply_a_camera_answer(self):
        for kind, answer in CASES.items():
            with self.subTest(kind=kind):
                result = self.score(kind, answer, f"<think>\n<answer>{answer}</answer>")
                self.assertTrue(result["parse_failed"])
                self.assertEqual(result["extract_branch"], "unclosed_thinking")
                self.assertEqual(result["response_text"], "")

    def test_native_stop_tokens_do_not_change_camera_answers(self):
        for kind, answer in CASES.items():
            with self.subTest(kind=kind):
                result = self.score(kind, answer, "</think>\n\n"+answer+"<|im_end|><|endoftext|>")
                self.assertFalse(result["parse_failed"])
                self.assertEqual(result["response_text"], answer)
                self.assertEqual(result["score"], 1)


if __name__ == "__main__":
    unittest.main()
