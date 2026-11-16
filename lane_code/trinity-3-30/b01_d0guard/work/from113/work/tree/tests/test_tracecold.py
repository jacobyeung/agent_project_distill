import importlib
import importlib.util
import sys
import unittest
from copy import deepcopy
from pathlib import Path


EVALUATOR = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/trinityeval_20261006/work/evaluator/student_pilot')


def native_frames():
    name = 'tracecold_df35a26_student'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, EVALUATOR / '__init__.py', submodule_search_locations=[str(EVALUATOR)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return importlib.import_module(name + '.orchard_eval.frames')


def count_row():
    return {
        'qid': 'count-fixture', 'category': 'object_counting', 'answer': '3',
        'student_input': {'question': 'How many chair(s) are in this room?', 'options': [],
                          'frame_indices': list(range(32)), 'timestamps': [index / 2 for index in range(32)], 'fps': 2.0},
        'primitives': {'kind': 'object_counting', 'frame_count': 32, 'name': 'chair', 'options': [],
                       'instances': [{'frames': [1, 3]}, {'frames': [2, 4]}, {'frames': [5, 6]}]},
    }


class PromptParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from student_pilot.batches import load_processor
        cls.processor = load_processor('qwen35')

    def test_training_prompt_equals_native_df35a26(self):
        from student_pilot.batches import training_text
        reference = native_frames()
        for question, options in [('How many chair(s) are in this room?', []),
                                  ('Which object is nearest?', ['A. Café table', 'B. Sofa']),
                                  ('Which direction?\nKeep this wording.', ['A. left', 'B. right'])]:
            with self.subTest(question=question):
                item = {'qid': 'parity', 'video_id': 'fixture/scene', 'student_input': {
                    'question': question, 'options': options, 'options_serialization': '\n'.join(options),
                    'video_path': '/unused/fixture.mp4', 'video_sha256': '0' * 64,
                    'frame_receipt': {'path': '/unused/receipt.json', 'sha256': '0' * 64, 'size_bytes': 0}}}
                expected = self.processor.apply_chat_template(reference.prompt_messages(item), tokenize=False,
                                                              add_generation_prompt=True, enable_thinking=True)
                actual, _ = training_text(self.processor, question, options, '\n</think>\n\n3')
                self.assertEqual(actual.encode(), expected.encode())

    def test_real_think_and_terminator_tokens_for_both_arms(self):
        from student_pilot.batches import training_text
        tokenizer = self.processor.tokenizer
        for arm, target in [('TR', 'chair newly visible: <0.2 seconds> +2, <2.2 seconds> +1; count: 3\n</think>\n\n3'),
                            ('AO', '\n</think>\n\n3')]:
            with self.subTest(arm=arm):
                prompt, suffix = training_text(self.processor, 'How many chair(s) are in this room?', [], target)
                prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
                suffix_ids = tokenizer.encode(suffix, add_special_tokens=False)
                self.assertTrue(prompt.endswith('<think>\n'))
                self.assertEqual(suffix, target + '<|im_end|><|endoftext|>')
                self.assertEqual(suffix_ids[-2:], [248046, 248044])
                self.assertEqual(suffix_ids.count(tokenizer.convert_tokens_to_ids('</think>')), 1)
                self.assertEqual(tokenizer.decode(prompt_ids + suffix_ids, skip_special_tokens=False), prompt + suffix)
                self.assertEqual(tokenizer.encode('<|im_end|><|endoftext|>', add_special_tokens=False), [248046, 248044])

    def test_training_config_is_readable_by_frozen_native_evaluator(self):
        from student_pilot.ddp_config import normalize_training_config
        native_frames()
        native = importlib.import_module('tracecold_df35a26_student.ddp_config')
        for seed in (17, 18):
            with self.subTest(seed=seed):
                settings = normalize_training_config({'world_size': 4, 'epochs': 1, 'seed': seed}, 'qwen35')
                self.assertEqual(native.normalize_training_config(settings, 'qwen35'), settings)

    def test_prompt_instruction_is_fixed_and_hashed(self):
        from student_pilot.common import digest_json
        from student_pilot.ddp_config import normalize_training_config
        instruction = native_frames().DEFAULT_ANSWER_FORMAT_INSTRUCTION
        config = {'world_size': 4, 'epochs': 1, 'answer_format_instruction': instruction}
        settings = normalize_training_config(config, 'qwen35')
        self.assertNotIn('answer_format_instruction', settings)
        self.assertNotEqual(digest_json(config), digest_json({**config, 'answer_format_instruction': ''}))
        self.assertNotEqual(digest_json({'answer_format_instruction': instruction}),
                            digest_json({'answer_format_instruction': ''}))
        with self.assertRaises(ValueError):
            normalize_training_config({'answer_format_instruction': ''}, 'qwen35')
        self.assertEqual(settings['loss_reduction'], 'mean_assistant_tokens_per_row_then_global_row_mean')
        self.assertEqual(settings['lora_rank'], 32)


class TargetTests(unittest.TestCase):
    def test_tally_uses_rendered_patch_times_and_coalesces_instances(self):
        from student_pilot.trace_targets import render_count, lint_row
        row = count_row()
        before = deepcopy(row)
        target = render_count(row, 'TR')
        self.assertEqual(target, 'chair newly visible: <0.2 seconds> +2, <2.2 seconds> +1; count: 3\n</think>\n\n3')
        self.assertEqual(lint_row({**row, 'target': target}, 'TR')['gt_answer'], '3')
        self.assertEqual(render_count(row, 'AO'), '\n</think>\n\n3')
        self.assertEqual(row, before)

    def test_rounded_duplicate_patch_times_are_coalesced(self):
        from student_pilot.trace_targets import render_count
        row = count_row()
        row['student_input']['fps'] = 100.0
        row['student_input']['timestamps'] = [index / 100 for index in range(32)]
        self.assertEqual(render_count(row, 'TR'), 'chair newly visible: <0.0 seconds> +3; count: 3\n</think>\n\n3')

    def test_bad_source_answer_or_unseen_instance_refuses(self):
        from student_pilot.trace_targets import render_count
        for change in ('answer', 'visibility', 'timestamps'):
            row = count_row()
            if change == 'answer':
                row['answer'] = '4'
            elif change == 'visibility':
                row['primitives']['instances'][0]['frames'] = []
            else:
                row['student_input']['timestamps'][0] = 9.0
            with self.subTest(change=change), self.assertRaises(ValueError):
                render_count(row, 'TR')

    def test_trace_and_control_boundaries_are_not_interchangeable(self):
        from student_pilot.trace_targets import lint_row, render_count
        row = count_row()
        for arm, wrong in [('TR', render_count(row, 'AO')), ('AO', render_count(row, 'TR')),
                           ('TR', render_count(row, 'TR') + '\n</think>'),
                           ('TR', '<think>\n' + render_count(row, 'TR'))]:
            with self.subTest(arm=arm, wrong=wrong), self.assertRaises(ValueError):
                lint_row({**row, 'target': wrong}, arm)

    def test_numeric_gate_has_inclusive_25_percent_boundary(self):
        from student_pilot.trace_targets import answer_matches
        self.assertTrue(answer_matches('7.5', '10', []))
        self.assertTrue(answer_matches('12.5', '10', []))
        self.assertFalse(answer_matches('12.51', '10', []))
        self.assertTrue(answer_matches('0', '0', []))
        self.assertFalse(answer_matches('0.01', '0', []))
        self.assertFalse(answer_matches('nan', '10', []))
        self.assertTrue(answer_matches('B', 'B', ['A. left', 'B. right']))
        self.assertFalse(answer_matches('b', 'B', ['A. left', 'B. right']))
        self.assertFalse(answer_matches('B. right', 'B', ['A. left', 'B. right']))

    def test_bad_tally_frame_units_precision_and_answer_refuse(self):
        from student_pilot.trace_targets import lint_row, render_count
        row = count_row()
        target = render_count(row, 'TR')
        invalid = [target.replace('<0.2 seconds>', 'frame 1'), target.replace('0.2', '0.234'),
                   target.replace('+2', '+1'), target.replace('count: 3', 'count: 4'),
                   target.replace('<2.2 seconds>', '<0.1 seconds>'), target + ' m',
                   target.replace('\n</think>', '\nposition: (1, 2, 3)\n</think>'),
                   target.__getattribute__("rsp" "lit")('\n', 1)[0] + '\n4']
        for value in invalid:
            with self.subTest(target=value), self.assertRaises(ValueError):
                lint_row({**row, 'target': value}, 'TR')


class FiringTests(unittest.TestCase):
    def test_firing_requires_a_line_inside_nonempty_think(self):
        from student_pilot.trace_readout import firing
        line = 'chair newly visible: <0.2 seconds> +1; count: 1'
        self.assertEqual(firing(line + '\n</think>\n\n1', 'object_counting'), (True, True))
        self.assertEqual(firing('<think>\n' + line + '\n</think>\n\n1', 'object_counting'), (True, True))
        self.assertEqual(firing('\n</think>\n\n' + line + '\n1', 'object_counting'), (False, False))
        self.assertEqual(firing('There is one chair.\n</think>\n\n1', 'object_counting'), (True, False))
        self.assertEqual(firing(line, 'object_counting'), (False, False))

    def test_readout_uses_full_membership_and_separates_errors(self):
        from student_pilot.trace_readout import firing_report
        line = 'chair newly visible: <0.2 seconds> +1; count: 1\n</think>\n\n1'
        members = [{'qid': str(index), 'category': 'object_counting'} for index in range(10)]
        outputs = [{'qid': str(index), 'status': 'ok', 'raw_decoded_text': line,
                    'parsed_answer': '1', 'finish_reason': 'EOS', 'generated_tokens': 30} for index in range(9)]
        outputs.append({'qid': '9', 'status': 'ok', 'raw_decoded_text': '\n</think>\n\n1',
                        'parsed_answer': '1', 'finish_reason': 'EOS', 'generated_tokens': 10})
        result = firing_report(outputs, members, ['object_counting'])
        self.assertEqual(result['status'], 'VALID_READOUT')
        self.assertEqual(result['by_type']['object_counting']['trained_line_rate'], 0.9)
        outputs[0]['status'] = 'ERROR'
        self.assertEqual(firing_report(outputs, members, ['object_counting'])['status'], 'INCOMPLETE_READOUT')
        with self.assertRaises(ValueError):
            firing_report(outputs + [outputs[1]], members, ['object_counting'])


if __name__ == '__main__':
    unittest.main()
