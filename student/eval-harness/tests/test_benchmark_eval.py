import builtins
import csv
import hashlib
import io
import json
import os
import struct
import subprocess
import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

from student_pilot.benchmark_eval import contracts, frames, generate, prepare, score
from student_pilot.benchmark_eval.answers import option_letters, parse_answer
from student_pilot.benchmark_eval.contracts import binding, digest, load_json, load_jsonl, write_bytes_once, write_once


REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / 'tests/fixtures/benchmark_eval'
PROJECT = Path(os.environ.get('STUDENT_EVAL_PROJECT_ROOT', '/home/jjyeung/agent_project'))
OUTPUT = Path(os.environ.get('STUDENT_EVAL_TEST_ROOT', str(REPO / 'artifacts/paper_eval/tests')))
OFFICIAL_PYTHON = os.environ.get('STUDENT_EVAL_OFFICIAL_PYTHON', '/data2/jjyeung/envs/planner/bin/python')
CONFIG = REPO / 'configs/student_benchmark_eval_v1.json'


def write_json(path, value, root):
    return write_once(path, value, root)


def synthetic_adapter(root, model='onethinker'):
    directory = root / ('adapter_' + uuid4().hex[:8])
    directory.mkdir(parents=True)
    config = {'peft_type': 'LORA', 'base_model_name_or_path': contracts.MODEL_PINS[model]['repo_id'],
              'target_modules': ['q_proj', 'linear_attn.in_proj_qkv', 'visual.proj'], 'r': 1, 'lora_alpha': 1}
    config_pin = write_json(directory / 'adapter_config.json', config, root)
    names = [f'base_model.model.{family}.lora_{kind}.weight' for family in ('visual', 'merger', 'language') for kind in ('A', 'B')]
    header = {name: {'dtype': 'F32', 'shape': [1, 1], 'data_offsets': [index * 4, (index + 1) * 4]} for index, name in enumerate(names)}
    encoded = json.dumps(header).encode()
    encoded += b' ' * ((8 - len(encoded) % 8) % 8)
    weights = len(encoded).to_bytes(8, 'little') + encoded + struct.pack('<6f', *range(6))
    weight_pin = write_bytes_once(directory / 'adapter_model.safetensors', weights, root)
    pin = contracts.MODEL_PINS[model]
    receipt = {'schema': 'clean-student-training-v1', 'status': 'TRAINED', 'synthetic': True,
               'benchmark_trained_diagnostic': False, 'smoke': False, 'dataset': 'VSI-590K',
               'base_restart': 'original_checkpoint', 'base': {key: pin[key] for key in ('repo_id', 'revision')},
               'preprocessing': contracts.RGB, 'enable_thinking': pin['enable_thinking'],
               'selection_frozen_before_benchmark': True, 'trained_module_families': ['vision', 'merger', 'language'],
               'training_data_sha256': 'a' * 64, 'scene_split_sha256': 'b' * 64,
               'adapter': {'config_sha256': config_pin['sha256'], 'weights_sha256': weight_pin['sha256']}}
    path = directory / 'training_receipt.json'
    write_json(path, receipt, root)
    return directory, path


class ParserTests(unittest.TestCase):
    def test_last_visible_answer_block_controls(self):
        result = parse_answer('<think><answer>D</answer></think><ANSWER>A</ANSWER><answer>b</answer>', ['A. red', 'B. blue'])
        self.assertEqual(result['answer'], 'B')
        self.assertEqual(result['parser']['complete_block_count'], 2)
        self.assertEqual(result['parser']['branch'], 'tag')

    def test_numeric_normalization_preserves_sign_and_exponent(self):
        for raw, expected in [('Final answer: -2e1', '-20.0'), ('<answer>+.5</answer>', '0.5'),
                              ('Answer: 6.', '6.0'), ('+12', '12.0'), ('-0', '-0.0'), ('0e999999', '0.0')]:
            with self.subTest(raw=raw):
                self.assertEqual(parse_answer(raw, [])['answer'], expected)

    def test_invalid_answers_fail_closed(self):
        for text in ('NaN', 'infinity', 'A or B', '<answer>A', '<answer>A</answer><answer>B',
                     '<think>A', 'The answer is A', '<answer><answer>A</answer>', '</answer>A'):
            with self.subTest(text=text):
                self.assertIsNone(parse_answer(text, ['A. red', 'B. blue'])['answer'])
        for text in ('NaN', '-inf', '1e309', '1,000', '2 meters', '1 2', '1/2', '', '<answer>2 or 3</answer>'):
            with self.subTest(text=text):
                self.assertIsNone(parse_answer(text, [])['answer'])

    def test_option_membership_and_native_eos(self):
        self.assertEqual(option_letters('A: red; B: blue; '), ['A', 'B'])
        self.assertEqual(parse_answer('B', 'A: red; B: blue;')['answer'], 'B')
        with self.assertRaises(ValueError):
            option_letters('A: red;; B: blue')
        self.assertIsNone(parse_answer('C', ['A. red', 'B. blue'])['answer'])
        self.assertEqual(parse_answer('Answer: B<|im_end|>', ['A. red', 'B. blue'])['answer'], 'B')
        self.assertEqual(parse_answer('reasoning\n\n final Answer: a\n', 'A: red;B: blue')['answer'], 'A')
        self.assertIsNone(parse_answer('Reasoning mentions A.\nNo final response.', ['A. red'])['answer'])
        for options in (['red', 'blue'], ['A. red', 'A. blue'], ['A. red', {'GT': 'B'}]):
            with self.subTest(options=options), self.assertRaises(ValueError):
                option_letters(options)


class SamplingTests(unittest.TestCase):
    def test_floor_uniform_selection(self):
        self.assertEqual(frames.sample_indices(45), [k * 44 // 31 for k in range(32)])
        self.assertEqual(frames.sample_indices(45), frames.sample_indices(45))
        self.assertEqual(frames.sample_indices(32), list(range(32)))
        for count in (0, 31, True, 32.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                frames.sample_indices(count)

    def test_unknown_fps_and_nonmonotonic_pts_are_rejected(self):
        indices = list(range(32))
        for fps in (None, 0, -1, float('nan')):
            with self.subTest(fps=fps), self.assertRaises(ValueError):
                frames.timing_audit(indices, fps, [i / 24 for i in indices])
        with self.assertRaises(ValueError):
            frames.timing_audit(indices, 24, [0.0] * 32)


class AdapterReloadTests(unittest.TestCase):
    def test_saved_fp32_and_bf16_adapter_values_and_dtypes_survive_loading(self):
        import torch
        import transformers
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from safetensors.torch import save_file

        class TinyBase(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.q_proj = torch.nn.Linear(3, 3, bias=False, dtype=torch.bfloat16)
                self.config = transformers.PretrainedConfig()

        root = OUTPUT / ('adapter_reload_' + uuid4().hex[:12])
        root.mkdir(parents=True)
        for model_name in ('onethinker', 'qwen35'):
            for dtype in (torch.float32, torch.bfloat16):
                with self.subTest(model=model_name, saved_dtype=str(dtype)):
                    adapter = root / f'{model_name}_{dtype}'
                    adapter.mkdir()
                    prototype = get_peft_model(TinyBase(), LoraConfig(r=1, lora_alpha=1, target_modules=['q_proj']))
                    config = prototype.peft_config['default'].to_dict()
                    config = {key: sorted(value) if isinstance(value, set) else value for key, value in config.items()}
                    config_pin = write_json(adapter / 'adapter_config.json', config, root)
                    original = get_peft_model_state_dict(prototype)
                    saved = {name: (torch.arange(value.numel(), dtype=torch.float32).reshape(value.shape) + 0.1234567).to(dtype)
                             for name, value in original.items()}
                    save_file(saved, str(adapter / 'adapter_model.safetensors'))
                    model_class = getattr(transformers, contracts.MODEL_PINS[model_name]['architecture'])
                    with mock.patch.object(model_class, 'from_pretrained', side_effect=lambda *args, **kwargs: TinyBase()):
                        loaded = generate.load_local_model(model_name, {'model': {'snapshot': str(adapter / 'unread_mock_base')}},
                                                           {'config': config_pin, 'weights': binding(adapter / 'adapter_model.safetensors')})
                    restored = get_peft_model_state_dict(loaded)
                    self.assertEqual(set(restored), set(saved))
                    for name in saved:
                        self.assertEqual(restored[name].dtype, saved[name].dtype)
                        self.assertTrue(torch.equal(restored[name].cpu(), saved[name]))
                    self.assertFalse(loaded.training)
                    self.assertTrue(all(not parameter.requires_grad for parameter in loaded.parameters()))


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite_root = OUTPUT / ('suite_' + uuid4().hex[:12])
        cls.suite_root.mkdir(parents=True)
        print(f'Preserved CPU fixture outputs: {cls.suite_root}', flush=True)
        cls.fixture = prepare.materialize_fixtures(FIXTURES, cls.suite_root / 'fixture', cls.suite_root)
        cls.prepared, cls.checks = {}, {}
        for benchmark, folder in zip(contracts.BENCHMARKS, ('vsibench', 'vstibench', 'dsibench')):
            output = cls.suite_root / folder
            prepare.prepare(benchmark, CONFIG, output, cls.suite_root, cls.fixture / folder,
                            cls.fixture / 'videos', cls.fixture / 'vsibench/MEMBERSHIP_ANSWERABLE_500.json',
                            project_root=PROJECT, synthetic=True)
            cls.prepared[benchmark] = output
            for model in ('onethinker', 'qwen35'):
                check = cls.suite_root / 'checks' / f'{folder}_{model}'
                frames.cpu_check(output / 'generation/manifest.json', model, check, cls.suite_root, synthetic=True)
                cls.checks[benchmark, model] = check / 'preflight.json'

    def setUp(self):
        self.root = self.suite_root / (self._testMethodName + '_' + uuid4().hex[:8])
        self.root.mkdir()

    def manifest(self, benchmark=contracts.BENCHMARKS[0]):
        return self.prepared[benchmark] / 'generation/manifest.json'

    def run_fake(self, benchmark=contracts.BENCHMARKS[0], model='onethinker', **kwargs):
        output = kwargs.pop('output', self.root / 'run')
        return generate.generate_run(self.manifest(benchmark), model, 'base', output, self.root,
                                     self.checks[benchmark, model], cpu_mock=True, **kwargs)

    def test_all_official_loaders_and_answer_free_schemas(self):
        for benchmark, count in zip(contracts.BENCHMARKS, (3, 3, 12)):
            manifest, rows, config = contracts.load_generation(self.manifest(benchmark))
            self.assertEqual(len(rows), count)
            self.assertEqual(manifest['expected_count'], count)
            self.assertFalse(manifest['paper_cell'])
            self.assertEqual(config, contracts.DEFAULT_CONFIG)
            for row in rows:
                self.assertEqual(set(row), {'qid', 'video_id', 'student_input'})
                contracts.reject_forbidden(row)
                self.assertNotIn('video_type', row['student_input'])
                self.assertNotIn('others', row['student_input'])
        _, rows, _ = contracts.load_generation(self.manifest())
        self.assertEqual(rows[0]['student_input']['options'], [])
        self.assertEqual(rows[2]['student_input']['options'], [])
        self.assertNotEqual(rows[0]['video_id'], rows[2]['video_id'])
        self.assertNotEqual(rows[0]['student_input']['video_path'], rows[2]['student_input']['video_path'])

    def test_cohort_joins_duplicate_missing_extra_and_hash_rejection(self):
        original = load_json(self.fixture / 'vsibench/answerable500_gt_canonical.json')
        membership = self.fixture / 'vsibench/MEMBERSHIP_ANSWERABLE_500.json'
        for name, rows in [('duplicate', original + [original[0]]), ('missing', original[:-1]),
                           ('extra', original + [{**original[0], 'id': 999999}])]:
            directory = self.root / name
            write_json(directory / 'answerable500_gt_canonical.json', rows, self.root)
            with self.subTest(case=name), self.assertRaises(ValueError):
                prepare.load_vsi(directory, self.fixture / 'videos', membership, PROJECT, synthetic=True)
        with self.assertRaises(ValueError):
            binding(membership, '0' * 64)
        path = self.root / 'bad_membership.json'
        write_json(path, {'qids_int_sorted': [900001, 900001]}, self.root)
        with self.assertRaises(ValueError):
            prepare.membership_rows(path)

    def test_malformed_mc_options_and_unknown_categories_fail(self):
        row = load_json(self.fixture / 'vsibench/answerable500_gt_canonical.json')[1]
        for changed in ({**row, 'options': []}, {**row, 'options': ['red', 'blue']}, {**row, 'question_type': 'invented'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                prepare._adapt_vsi_rows([changed], self.fixture / 'videos', prepare.VSI_CATEGORIES, None)

    def test_real_cohort_guard_rejects_retirement_and_checks_admission(self):
        manifest = load_json(self.manifest())
        inspected = contracts.guard_inputs(manifest['guard']['source'], manifest['guard']['registry'],
                                           [manifest['membership']['path'], manifest['admission_input']['path']])
        self.assertEqual(len(inspected), 2)
        self.assertTrue(all(not row['matches'] for row in inspected))
        guard = contracts.import_file(manifest['guard']['source']['path'], 'test_real_cohort_guard')
        registry = {'schema': 'retired-cohorts-v1', 'cohorts': [{'name': 'synthetic-retired',
                    'membership_sha256': manifest['membership']['sha256'], 'qid_set_sha256': guard.qid_set_sha256([900001, 900002, 900003]),
                    'replacement': {'name': 'active', 'path': 'fixture.json', 'sha256': 'a' * 64}, 'allowed_uses': []}]}
        pin = write_json(self.root / 'registry.json', registry, self.root)
        with self.assertRaises(guard.RetiredCohortError):
            guard.guard_cohort(manifest['admission_input']['path'], registry_path=pin['path'])

    def test_canonical_vsti_authority_and_mapping_pins(self):
        binding(PROJECT / 'agent/vstibench_repr_450_v2.json', prepare.VSTI_SHA)
        binding(PROJECT / 'agent/vstibench_repr_450_v2.json.provenance', prepare.VSTI_PROVENANCE_SHA)
        source = load_json(self.fixture / 'vstibench/vstibench_repr_450_v2.json')
        source[0]['answer_mapping']['text'] = 'incorrect mapping'
        directory = self.root / 'bad_vsti'
        pin = write_json(directory / 'vstibench_repr_450_v2.json', source, self.root)
        write_json(directory / 'vstibench_repr_450_v2.json.provenance',
                   {'schema': 'vstibench-repr450-v2-canonical-provenance-v1', 'artifact': {'rows': 3, 'sha256': pin['sha256']}}, self.root)
        with self.assertRaisesRegex(ValueError, 'mapping'):
            prepare.load_vsti(directory, self.fixture / 'videos', synthetic=True)

    def test_dsi_verbatim_options_groups_and_variant_alignment(self):
        adapted, _, _, _ = prepare.load_dsi(self.fixture / 'dsibench', synthetic=True)
        self.assertEqual(len(adapted), 12)
        self.assertEqual(len({row['qid'] for row in adapted}), 12)
        self.assertEqual(len({row['video_id'] for row in adapted}), 4)
        with (self.fixture / 'dsibench/metadatas/reverse.csv').open(newline='') as handle:
            original = list(csv.DictReader(handle))
        row = next(row for row in adapted if row['qid'] == 'dsibench:reverse:0')
        self.assertEqual(row['question'], original[0]['question'])
        self.assertEqual(row['options'], original[0]['options'])
        self.assertNotEqual(row['options'], adapted[0]['options'])
        self.assertEqual(row['label']['group_id'], 0)
        write_json(self.root / 'metadata_4aug.csv', {'not_an_additional_cohort': True}, self.root)
        for action in ('reordered', 'missing'):
            root = self.root / action
            root.mkdir()
            source_manifest = load_json(self.fixture / 'dsibench/MANIFEST.json')
            for variant in contracts.VARIANTS:
                path = self.fixture / f'dsibench/metadatas/{variant}.csv'
                with path.open(newline='') as handle:
                    records = list(csv.DictReader(handle))
                if variant == 'reverse':
                    records = list(reversed(records)) if action == 'reordered' else records[:-1]
                payload = score.csv_bytes(list(records[0]), records)
                new_pin = write_bytes_once(root / f'metadatas/{variant}.csv', payload, self.root)
                for entry in source_manifest['files']:
                    if entry['path'] == f'metadatas/{variant}.csv':
                        entry.update(sha256=new_pin['sha256'], size_bytes=new_pin['size_bytes'])
            write_json(root / 'MANIFEST.json', source_manifest, self.root)
            with self.subTest(action=action), self.assertRaises(ValueError):
                prepare.load_dsi(root, synthetic=True)

    def test_exact_frame_decode_pixels_hashes_and_reuse(self):
        _, rows, _ = contracts.load_generation(self.manifest())
        item = rows[0]['student_input']
        arrays, receipt = frames.load_selection(item['frame_receipt'])
        self.assertEqual(receipt['frame_indices'], frames.sample_indices(40))
        self.assertEqual(arrays.shape, (32, 32, 64, 3))
        self.assertEqual(receipt['fps_rational'], {'numerator': 24, 'denominator': 1})
        for array, source in zip(arrays, receipt['frames']):
            self.assertEqual(int(array[0, 0, 0]), source['index'])
            self.assertEqual(hashlib.sha256(array.tobytes()).hexdigest(), source['rgb_sha256'])
            binding(source['png']['path'], source['png']['sha256'])
        pin = frames.cache_selection(item['video_path'], self.root / 'cache', self.root)
        cached = frames.cache_selection(item['video_path'], self.root / 'cache', self.root)
        self.assertEqual(pin, cached)
        self.assertEqual(load_json(pin['path'])['ordered_selection_sha256'], receipt['ordered_selection_sha256'])

    def test_corrupt_cache_and_short_video_are_rejected(self):
        _, rows, _ = contracts.load_generation(self.manifest())
        pin = frames.cache_selection(rows[0]['student_input']['video_path'], self.root / 'cache', self.root)
        receipt = load_json(pin['path'])
        frame = Path(receipt['frames'][0]['png']['path'])
        with frame.open('ab') as handle:
            handle.write(b'corrupt')
        with self.assertRaises(ValueError):
            frames.load_selection(pin)
        short = self.root / 'short.mp4'
        prepare.create_fixture_video(short, FIXTURES / 'frames', self.root, count=31)
        with self.assertRaisesRegex(ValueError, '32'):
            frames.cache_selection(short, self.root / 'short_cache', self.root)

    def test_variable_rate_pts_remain_distinct_from_native_timestamps(self):
        video = self.root / 'variable.mp4'
        prepare.create_fixture_video(video, FIXTURES / 'frames', self.root, count=40, variable_rate=True)
        pin = frames.cache_selection(video, self.root / 'cache', self.root)
        _, receipt = frames.load_selection(pin)
        timing = frames.timing_audit(receipt['frame_indices'], receipt['fps'], [row['pts_seconds'] for row in receipt['frames']])
        self.assertFalse(timing['constant_rate_timing_exact'])
        self.assertGreater(timing['max_frame_timestamp_discrepancy_seconds'], 0)
        self.assertEqual(len(timing['effective_timestamps_seconds']), 16)
        self.assertEqual(len(timing['source_pts_seconds']), 32)

    def test_prompt_and_pixel_equality_with_training_encoder(self):
        import torch
        from student_pilot.batches import encode_arrays
        from transformers.video_utils import VideoMetadata

        _, rows, config = contracts.load_generation(self.manifest())
        row = rows[1]
        arrays, receipt = frames.load_selection(row['student_input']['frame_receipt'])
        processor = frames.SyntheticProcessor()
        metadata = VideoMetadata(total_num_frames=receipt['total_num_frames'], fps=receipt['fps'],
                                 frames_indices=receipt['frame_indices'], width=64, height=32)
        trained, training_audit = encode_arrays(processor, row['student_input']['question'], row['student_input']['options'],
                                                arrays, metadata, '<answer>A</answer>')
        packed, audit = frames.pack_input(processor, row, 'onethinker', config)
        length = training_audit['prompt_tokens']
        torch.testing.assert_close(packed['input_ids'], trained['input_ids'][:, :length])
        torch.testing.assert_close(packed['pixel_values_videos'], trained['pixel_values_videos'])
        torch.testing.assert_close(packed['video_grid_thw'], trained['video_grid_thw'])
        self.assertNotIn('labels', packed)
        self.assertEqual(audit['prompt_tokens'], length)
        self.assertEqual(frames.prompt_messages(row)[0]['content'][1]['text'], row['student_input']['question'] + '\n' + '\n'.join(row['student_input']['options']))
        self.assertFalse(audit['do_sample_frames'])

    def test_native_template_policy_and_no_input_truncation(self):
        import torch
        _, rows, config = contracts.load_generation(self.manifest())
        processor = frames.SyntheticProcessor()
        _, one = frames.pack_input(processor, rows[0], 'onethinker', config)
        _, qwen = frames.pack_input(processor, rows[0], 'qwen35', config)
        self.assertFalse(one['prompt'].endswith('<think>\n'))
        self.assertTrue(qwen['prompt'].endswith('<think>\n'))
        original = processor.__class__.__call__
        def oversize(this, **kwargs):
            result = original(this, **kwargs)
            result['input_ids'] = torch.cat((result['input_ids'], torch.full((1, 16385), 300, dtype=torch.long)), dim=1)
            result['attention_mask'] = torch.ones_like(result['input_ids'])
            return result
        with mock.patch.object(frames.SyntheticProcessor, '__call__', oversize), self.assertRaisesRegex(ValueError, 'cap'):
            frames.pack_input(processor, rows[0], 'onethinker', config)

    def test_nested_forbidden_inputs_and_output_escape_refused(self):
        _, rows, _ = contracts.load_generation(self.manifest())
        for field in ('GT', 'ground_truth', 'answer_mapping', 'teacher_outputs', 'target', 'geometry'):
            changed = deepcopy(rows[0])
            changed['student_input']['options'] = [{'extra': {field: 'canary'}}]
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.validate_input(changed)
        with self.assertRaises(ValueError):
            write_json(self.root / '../escape.json', {}, self.root)
        sibling = self.suite_root / ('outside_' + uuid4().hex[:8])
        sibling.mkdir()
        (self.root / 'escape').symlink_to(sibling, target_is_directory=True)
        with self.assertRaises(ValueError):
            write_json(self.root / 'escape/value.json', {}, self.root)
        with self.assertRaises(ValueError):
            contracts.output_path('/home/student_eval_fixture/paper.json', '/home/student_eval_fixture', paper=True)
        pin = write_json(self.root / 'once.json', {'a': 1}, self.root)
        with self.assertRaises(ValueError):
            write_json(pin['path'], {'a': 1}, self.root)

    def test_inference_import_closure_never_opens_preparation_or_labels(self):
        program = """import sys
blocked = ('/benchmark_eval/prepare.', '/benchmark_eval/score.', '/student_pilot/diagnostic', '/student_pilot/admission.', '/student_pilot/conversion.')
def audit(event, args):
    if event == 'open' and isinstance(args[0], str) and any(name in args[0] for name in blocked):
        raise RuntimeError('Forbidden inference import read: ' + args[0])
sys.addaudithook(audit)
import student_pilot.benchmark_eval.generate
assert not any(name in sys.modules for name in ('student_pilot.diagnostic_data', 'student_pilot.benchmark_eval.prepare', 'student_pilot.benchmark_eval.score'))
print('ISOLATED_INFERENCE_IMPORT_PASS')
"""
        result = subprocess.run([sys.executable, '-B', '-c', program], capture_output=True, text=True, check=True,
                                cwd=REPO, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
        self.assertIn('ISOLATED_INFERENCE_IMPORT_PASS', result.stdout)

    def test_fake_generation_cannot_read_canary_gt_teacher_or_scorer(self):
        forbidden = {str(self.prepared[contracts.BENCHMARKS[0]] / 'scoring/labels.jsonl'),
                     str(PROJECT / 'agent/evaluation/scoring.py')}
        canary = self.root / 'teacher_canary.json'
        write_json(canary, {'GT': 'UNAVAILABLE_TO_GENERATION'}, self.root)
        forbidden.add(str(canary))
        active, reads = [True], []
        def audit(event, args):
            if active[0] and event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)) and os.fsdecode(args[0]) in forbidden:
                reads.append(os.fsdecode(args[0]))
                raise PermissionError('Forbidden scoring/teacher read')
        sys.addaudithook(audit)
        try:
            with self.assertRaises(PermissionError):
                canary.read_bytes()
            reads.clear()
            result = self.run_fake()
        finally:
            active[0] = False
        self.assertEqual(reads, [])
        self.assertEqual(result['started_count'], 3)
        self.assertFalse(result['offline_scoring_performed'])

    def test_changed_gt_does_not_change_generation_inputs_or_fake_outputs(self):
        self.run_fake()
        first = load_jsonl(self.root / 'run/generations.jsonl')
        source = self.fixture / 'vsibench/answerable500_gt_canonical.json'
        changed = load_json(source)
        changed[0]['ground_truth'] = '500'
        changed[1]['ground_truth'] = 'B'
        root = self.root / 'changed_labels'
        write_json(root / 'answerable500_gt_canonical.json', changed, self.root)
        adapted, _, _, _ = prepare.load_vsi(root, self.fixture / 'videos', self.fixture / 'vsibench/MEMBERSHIP_ANSWERABLE_500.json', PROJECT, synthetic=True)
        _, public_rows, _ = contracts.load_generation(self.manifest())
        for new, public in zip(adapted, public_rows):
            self.assertEqual(new['question'], public['student_input']['question'])
            self.assertEqual(new['options'], public['student_input']['options'])
        alternate_root = self.root / 'independent_fake_scope'
        alternate_root.mkdir()
        generate.generate_run(self.manifest(), 'onethinker', 'base', alternate_root / 'run', alternate_root,
                              self.checks[contracts.BENCHMARKS[0], 'onethinker'], cpu_mock=True)
        second = load_jsonl(alternate_root / 'run/generations.jsonl')
        for left, right in zip(first, second):
            for field in ('raw_generation', 'generated_token_ids', 'parsed_answer', 'parser', 'input_audit'):
                self.assertEqual(left[field], right[field])

    def test_real_writer_jsonl_schema_eos_and_idempotent_resume(self):
        completion = self.run_fake()
        header = load_json(self.root / 'run/run.json')
        records = load_jsonl(self.root / 'run/generations.jsonl')
        self.assertEqual(completion['started_count'], 3)
        self.assertEqual(len(records), 3)
        for record in records:
            contracts.validate_receipt(record, header)
            self.assertEqual(record['finish_reason'], 'eos')
            self.assertEqual(len(record['frame_hashes']), 32)
            self.assertEqual(len(record['frame_indices']), 32)
            self.assertEqual(record['generated_tokens'], len(record['generated_token_ids']))
            self.assertIsNone(record['peak_allocated_bytes'])
        boundary = mock.Mock(side_effect=AssertionError('Resume called the model twice'))
        self.run_fake(resume=True, generator=boundary)
        boundary.assert_not_called()
        self.assertEqual(len(load_jsonl(self.root / 'run/attempts.jsonl')), 3)

    def test_resume_after_final_jsonl_publication_never_regenerates(self):
        self.run_fake()
        run = self.root / 'run'
        generations_hash = binding(run / 'generations.jsonl')['sha256']
        quarantine = run / '_quarantine'
        quarantine.mkdir()
        (run / 'completion.json').rename(quarantine / 'completion_before_simulated_crash.json')
        boundary = mock.Mock(side_effect=AssertionError('A finalized answer was regenerated'))
        completion = self.run_fake(resume=True, generator=boundary)
        boundary.assert_not_called()
        self.assertEqual(completion['terminal_count'], 3)
        self.assertEqual(binding(run / 'generations.jsonl')['sha256'], generations_hash)
        self.assertEqual(len(load_jsonl(run / 'attempts.jsonl')), 3)

    def test_started_generation_error_is_terminal_and_never_retried(self):
        boundary = mock.Mock(side_effect=RuntimeError('synthetic model failure'))
        result = self.run_fake(generator=boundary)
        self.assertEqual(boundary.call_count, 3)
        self.assertEqual(result['started_count'], 3)
        self.assertEqual(set(result['outcomes'].values()), {'generation_error'})
        self.run_fake(resume=True, generator=boundary)
        self.assertEqual(boundary.call_count, 3)
        for row in load_jsonl(self.root / 'run/generations.jsonl'):
            self.assertIsNone(row['generated_tokens'])
            self.assertIsNone(row['raw_generation'])

    def test_unexpected_stop_preserves_native_output_but_scores_zero(self):
        def unexpected(batch, audit, config):
            text = '<answer>A</answer>'
            return {'tokens': frames.SyntheticTokenizer().encode(text), 'raw': text, 'display': text}
        self.run_fake(generator=unexpected)
        records = load_jsonl(self.root / 'run/generations.jsonl')
        self.assertTrue(all(row['status'] == 'generation_error' for row in records))
        self.assertEqual(records[1]['raw_generation'], '<answer>A</answer>')
        self.assertEqual(records[1]['parsed_answer'], 'A')
        self.assertGreater(records[1]['generated_tokens'], 0)
        result = score.score_run(self.root / 'run', self.prepared[contracts.BENCHMARKS[0]] / 'scoring/manifest.json',
                                 self.root / 'score', self.root)
        self.assertEqual(result['primary_score'], 0)
        self.assertEqual(result['started_count'], 3)

    def test_interrupted_start_and_output_publication_do_not_repeat_attempt(self):
        class SimulatedDeath(BaseException):
            pass
        for stage in ('after_start', 'before_publish'):
            root = self.root / stage
            root.mkdir()
            calls = []
            def stop(event, qid):
                if event == stage:
                    raise SimulatedDeath()
            def boundary(batch, audit, config):
                calls.append(audit['qid'])
                text = '<answer>A</answer><|im_end|>'
                return {'tokens': frames.SyntheticTokenizer().encode(text), 'raw': text, 'display': '<answer>A</answer>'}
            with self.assertRaises(SimulatedDeath):
                generate.generate_run(self.manifest(), 'onethinker', 'base', root / 'run', root,
                                      self.checks[contracts.BENCHMARKS[0], 'onethinker'], cpu_mock=True,
                                      generator=boundary, test_hook=stop)
            completion = generate.generate_run(self.manifest(), 'onethinker', 'base', root / 'run', root,
                                               self.checks[contracts.BENCHMARKS[0], 'onethinker'], cpu_mock=True,
                                               generator=boundary, resume=True)
            self.assertEqual(completion['interrupted_count'], 1)
            self.assertEqual(len(calls), 2 if stage == 'after_start' else 3)
            self.assertEqual(len(set(calls)), len(calls))
            self.assertEqual(len(load_jsonl(root / 'run/attempts.jsonl')), 3)

    def test_duplicate_run_and_concurrent_authority_are_refused(self):
        self.run_fake()
        boundary = mock.Mock()
        with self.assertRaises(ValueError):
            self.run_fake(output=self.root / 'second', generator=boundary)
        boundary.assert_not_called()
        lock = self.root / 'test.lock'
        with contracts.exclusive_lock(lock, self.root):
            with self.assertRaises(ValueError):
                with contracts.exclusive_lock(lock, self.root):
                    self.fail('Concurrent authority lock was acquired')

    def test_decode_or_runtime_drift_is_refused_before_model_boundary(self):
        preflight = load_json(self.checks[contracts.BENCHMARKS[0], 'onethinker'])
        for field in ('decoding', 'runtime'):
            changed = deepcopy(preflight)
            if field == 'decoding':
                changed['effective_generation_config']['max_new_tokens'] = 32768
            else:
                changed['runtime'] = []
            path = self.root / f'{field}.json'
            write_json(path, changed, self.root)
            boundary = mock.Mock()
            with self.subTest(field=field), self.assertRaises(ValueError):
                generate.generate_run(self.manifest(), 'onethinker', 'base', self.root / field, self.root, path,
                                      cpu_mock=True, generator=boundary)
            boundary.assert_not_called()
        changed_config = deepcopy(contracts.DEFAULT_CONFIG)
        changed_config['decoding']['seed'] = 18
        path = self.root / 'bad_config.json'
        write_json(path, changed_config, self.root)
        with self.assertRaises(ValueError):
            contracts.load_config(path)

    def test_exact_cap_keeps_completed_answer_without_a_retry(self):
        def capped(batch, audit, config):
            text = '<answer>A</answer>'
            tokens = frames.SyntheticTokenizer().encode(text)
            tokens += [ord('x') + 256] * (16384 - len(tokens))
            return {'tokens': tokens, 'raw': text + 'x' * (16384 - len(text)), 'display': text}
        boundary = mock.Mock(side_effect=capped)
        self.run_fake(generator=boundary)
        records = load_jsonl(self.root / 'run/generations.jsonl')
        self.assertTrue(all(row['finish_reason'] == 'max_new_tokens' for row in records))
        self.assertEqual(records[1]['parsed_answer'], 'A')
        self.assertEqual(boundary.call_count, 3)

    def test_vsi_scoring_matches_pinned_numeric_mra_and_zero_target(self):
        pins = load_json(self.prepared[contracts.BENCHMARKS[0]] / 'scoring/manifest.json')['scorer']
        scorer, core = score.canonical_scorer(pins)
        for target, raw in [('10', '8'), ('0', '0'), ('10', ''), ('10', '1e1')]:
            parsed = parse_answer(raw, [])['answer']
            trace = {'question_id': '1', 'trace': {'messages': [{'role': 'ai', 'content': f'<ANSWER>{parsed}</ANSWER>' if parsed else ''}]}}
            label = {'id': '1', 'question_type': 'object_abs_distance', 'ground_truth': target}
            record, _ = scorer._score_entry(trace, label, strict=True)
            expected = scorer.mean_relative_accuracy(float(parsed) if parsed else None, float(target), 0.5, 0.95, 0.05)
            self.assertEqual(record['MRA'], expected)
        self.assertEqual(scorer.mean_relative_accuracy(0, 0, 0.5, 0.95, 0.05), 0.0)
        self.assertNotEqual(scorer.mean_relative_accuracy(8, 10, 0.5, 0.95, 0.05), 1.0)
        values = {name: (0.0 if name.startswith('object_rel_direction') else 1.0) for name in prepare.VSI_CATEGORIES}
        result = score.aggregate_categories(values, contracts.BENCHMARKS[0], scorer, core)
        self.assertEqual(result['primary_score'], 7 / 8)

    def test_vsti_official_five_subtasks_not_nine_category_macro(self):
        pins = load_json(self.prepared[contracts.BENCHMARKS[1]] / 'scoring/manifest.json')['scorer']
        scorer, core = score.canonical_scorer(pins)
        values = {name: (0.0 if name.startswith('camera_obj_rel_dist') or name.startswith('obj_obj_relative_pos') else 1.0)
                  for name in prepare.VSTI_CATEGORIES}
        result = score.aggregate_categories(values, contracts.BENCHMARKS[1], scorer, core)
        self.assertEqual(result['primary_score'], 0.6)
        self.assertAlmostEqual(result['raw_category_macro'], 1 / 3)
        with self.assertRaises(ValueError):
            score.aggregate_categories({**values, 'unknown': 1.0}, contracts.BENCHMARKS[1], scorer, core)
        values.pop('camera_displacement')
        with self.assertRaises(ValueError):
            score.aggregate_categories(values, contracts.BENCHMARKS[1], scorer, core)

    def test_dsi_four_variants_count_correctness_not_majority_letter(self):
        labels, answers = [], {}
        for index, variant in enumerate(contracts.VARIANTS):
            for group, correct in enumerate((0, 2, 3, 4)):
                qid, letter = f'dsibench:{variant}:{group}', 'ABCD'[index]
                labels.append({'id': qid, 'variant': variant, 'group_id': group, 'question_type': str(group),
                               'relative_path': 'synthetic/clip.mp4', 'ground_truth': letter,
                               'question': 'Which synthetic direction?', 'options': 'A: left;B: right;C: up;D: down'})
                answers[qid] = letter if index < correct else None
        answers = dict(reversed(list(answers.items())))
        metrics, credits = score.dsi_metrics(labels, answers)
        self.assertEqual(metrics['group_credits'], {'0': 0, '1': 0, '2': 1, '3': 1})
        self.assertEqual(metrics['group_wise_accuracy'], 0.5)
        self.assertEqual(metrics['primary_score'], 9 / 16)
        self.assertEqual(len(credits), 16)
        observed, _ = score.official_dsi(labels, answers,
                                        binding(FIXTURES / 'dsibench/official_repo/evaluate.py', prepare.DSI_SCORER_SHA),
                                        self.root / 'official', self.root, False, OFFICIAL_PYTHON)
        self.assertEqual(observed['values'][0]['overall'], 9 / 16)
        self.assertIn('Overall Acc = 56.25%', observed['printed'])
        with self.assertRaises(ValueError):
            score.dsi_metrics(labels[:-1], answers)
        with self.assertRaises(ValueError):
            score.dsi_metrics(labels, {**answers, 'unexpected': 'A'})

    def test_offline_score_replay_preserves_native_artifacts(self):
        for benchmark in contracts.BENCHMARKS:
            root = self.root / benchmark
            root.mkdir()
            generate.generate_run(self.manifest(benchmark), 'onethinker', 'base', root / 'run', root,
                                  self.checks[benchmark, 'onethinker'], cpu_mock=True)
            before = {path.name: binding(path)['sha256'] for path in (root / 'run/questions').glob('*.json')}
            manifest = self.prepared[benchmark] / 'scoring/manifest.json'
            first = score.score_run(root / 'run', manifest, root / 'score1', root, OFFICIAL_PYTHON)
            second = score.score_run(root / 'run', manifest, root / 'score2', root, OFFICIAL_PYTHON)
            self.assertEqual(first['primary_score'], second['primary_score'])
            self.assertEqual(first['per_question_scores']['sha256'], second['per_question_scores']['sha256'])
            self.assertTrue(first['coverage_complete'])
            self.assertEqual(before, {path.name: binding(path)['sha256'] for path in (root / 'run/questions').glob('*.json')})
            self.assertEqual(first['expected_count'], len(load_jsonl(root / 'run/generations.jsonl')))

    def test_missing_receipts_receive_zero_with_unchanged_denominator(self):
        class SimulatedDeath(BaseException):
            pass
        def stop(stage, qid):
            if stage == 'after_start':
                raise SimulatedDeath()
        with self.assertRaises(SimulatedDeath):
            self.run_fake(test_hook=stop)
        result = score.score_run(self.root / 'run', self.prepared[contracts.BENCHMARKS[0]] / 'scoring/manifest.json',
                                 self.root / 'score', self.root)
        self.assertEqual(result['expected_count'], 3)
        self.assertEqual(result['missing_count'], 3)
        self.assertFalse(result['coverage_complete'])
        self.assertEqual(result['primary_score'], 0)
        self.assertEqual(len(load_jsonl(result['per_question_scores']['path'])), 3)

    def test_clean_lineage_validation_and_base_independence(self):
        self.assertIsNone(contracts.validate_adapter('base', 'onethinker', None, None, contracts.DEFAULT_CONFIG))
        adapter, path = synthetic_adapter(self.root)
        with self.assertRaises(ValueError):
            contracts.validate_adapter('distilled', 'onethinker', adapter, path, contracts.DEFAULT_CONFIG)
        accepted = contracts.validate_adapter('distilled', 'onethinker', adapter, path, contracts.DEFAULT_CONFIG, allow_synthetic=True)
        self.assertEqual(accepted['weights']['sha256'], binding(adapter / 'adapter_model.safetensors')['sha256'])
        receipt = load_json(path)
        for key, value in [('benchmark_trained_diagnostic', True), ('smoke', True), ('dataset', 'benchmark'),
                           ('preprocessing', {}), ('base', {}), ('selection_frozen_before_benchmark', False)]:
            changed = {**receipt, key: value}
            new_path = self.root / (key + '.json')
            write_json(new_path, changed, self.root)
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.validate_adapter('distilled', 'onethinker', adapter, new_path, contracts.DEFAULT_CONFIG, allow_synthetic=True)
        with self.assertRaises(ValueError):
            contracts.validate_adapter('distilled', 'qwen35', adapter, path, contracts.DEFAULT_CONFIG)
        with self.assertRaises(ValueError):
            contracts.validate_adapter('distilled', 'onethinker', None, None, contracts.DEFAULT_CONFIG)

    def test_pair_rejects_settings_frame_prompt_membership_model_scorer_drift(self):
        self.run_fake()
        base = load_json(self.root / 'run/run.json')['core']
        distilled = deepcopy(base)
        distilled.update(variant='distilled', adapter={'clean': True}, protocol_sha256='a' * 64)
        distilled['model_identity']['adapter_manifest_sha256'] = 'b' * 64
        contracts.require_pair(base, distilled)
        for field in ('config', 'decoding', 'input_audits_sha256', 'ordered_ids', 'generation_manifest', 'model_snapshot', 'runtime'):
            changed = deepcopy(distilled)
            changed[field] = {'changed': True}
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.require_pair(base, changed)

    def test_distilled_generation_requires_a_matching_base_and_compares_offline(self):
        self.run_fake()
        adapter, receipt = synthetic_adapter(self.root)
        check = self.root / 'distilled_check'
        frames.cpu_check(self.manifest(), 'onethinker', check, self.root, synthetic=True,
                         variant='distilled', adapter=adapter, training_receipt=receipt)
        boundary = mock.Mock()
        with self.assertRaisesRegex(ValueError, 'base-run'):
            generate.generate_run(self.manifest(), 'onethinker', 'distilled', self.root / 'missing_pair', self.root,
                                  check / 'preflight.json', adapter=adapter, training_receipt=receipt,
                                  cpu_mock=True, generator=boundary)
        boundary.assert_not_called()
        bad_base = load_json(self.root / 'run/run.json')
        bad_base['core']['input_audits_sha256'] = '0' * 64
        write_json(self.root / 'bad_base/run.json', bad_base, self.root)
        with self.assertRaisesRegex(ValueError, 'settings differ'):
            generate.generate_run(self.manifest(), 'onethinker', 'distilled', self.root / 'bad_pair', self.root,
                                  check / 'preflight.json', adapter=adapter, training_receipt=receipt, cpu_mock=True,
                                  generator=boundary, paired_base_run=self.root / 'bad_base')
        boundary.assert_not_called()
        generate.generate_run(self.manifest(), 'onethinker', 'distilled', self.root / 'distilled', self.root,
                              check / 'preflight.json', adapter=adapter, training_receipt=receipt,
                              cpu_mock=True, paired_base_run=self.root / 'run')
        manifest = self.prepared[contracts.BENCHMARKS[0]] / 'scoring/manifest.json'
        score.score_run(self.root / 'run', manifest, self.root / 'base_score', self.root)
        score.score_run(self.root / 'distilled', manifest, self.root / 'distilled_score', self.root)
        comparison = score.compare_scores(self.root / 'base_score/scores.json', self.root / 'distilled_score/scores.json',
                                          self.root / 'comparison', self.root)
        self.assertEqual(comparison['delta_percentage_points'], 0)
        self.assertTrue(comparison['coverage_complete'])
        duplicate_adapter, duplicate_receipt = synthetic_adapter(self.root)
        duplicate_check = self.root / 'duplicate_distilled_check'
        frames.cpu_check(self.manifest(), 'onethinker', duplicate_check, self.root, synthetic=True,
                         variant='distilled', adapter=duplicate_adapter, training_receipt=duplicate_receipt)
        with self.assertRaisesRegex(ValueError, 'attempt authority'):
            generate.generate_run(self.manifest(), 'onethinker', 'distilled', self.root / 'duplicate_distilled', self.root,
                                  duplicate_check / 'preflight.json', adapter=duplicate_adapter, training_receipt=duplicate_receipt,
                                  cpu_mock=True, generator=boundary, paired_base_run=self.root / 'run')
        boundary.assert_not_called()

    def test_qwen_native_generation_config_without_generation_json(self):
        from transformers import GenerationConfig, Qwen3_5Config
        native = GenerationConfig.from_model_config(Qwen3_5Config())
        if native.eos_token_id is None:
            native.eos_token_id = 10
        config = generate.effective_generation_config(native, frames.SyntheticProcessor())
        self.assertEqual(config.eos_token_id, native.eos_token_id)
        self.assertEqual(config.max_new_tokens, 16384)
        self.assertIsNone(config.temperature)
        self.assertIsNone(config.top_k)
        self.assertIsNone(config.top_p)
        self.assertTrue(config.use_cache)

    def test_lease_validator_enforces_evaluation_placement_and_authenticates_coord(self):
        now = datetime.now(timezone.utc)
        work = contracts.work_id(contracts.BENCHMARKS[0], 'onethinker', 'base', 'f' * 64)
        evidence_path = self.root / f'coord/LEASES/{work}.lock/lease.json'
        lease = {'host': 'trinity-2-28', 'gpu_index': 0, 'ownership_check_passed': True,
                 'coordination_lease_passed': True, 'vnice_wrapped': True, 'owner': 'fixture-owner',
                 'work_id': work, 'coordination_lease_evidence': str(evidence_path), 'protocol_sha256': 'f' * 64,
                 'ownership_checked_at': now.isoformat(), 'expires_at': (now + timedelta(hours=1)).isoformat(),
                 'gpu_uuid': 'GPU-synthetic-fixture'}
        for key, value in [(None, None), ('host', 'trinity-1-13'), ('gpu_index', 2), ('vnice_wrapped', False),
                           ('ownership_checked_at', (now - timedelta(minutes=6)).isoformat()),
                           ('expires_at', (now - timedelta(seconds=1)).isoformat())]:
            changed = dict(lease)
            if key:
                changed[key] = value
            if key is None:
                contracts.check_lease(changed, 'trinity-2-28', '0', now)
            else:
                with self.assertRaises(ValueError):
                    contracts.check_lease(changed, 'trinity-2-28', '0', now)
        with self.assertRaises(ValueError):
            contracts.check_lease({**lease, 'host': 'trinity-1-8'}, 'trinity-1-8', '0', now)
        write_json(evidence_path, {'work_id': work, 'agent_id': lease['owner'], 'status': 'running',
                                  'host': 'trinity-2-28', 'last_heartbeat': now.isoformat()}, self.root)
        lease_path = self.root / 'lease.json'
        write_json(lease_path, lease, self.root)
        result = contracts.authenticate_lease(lease_path, work, 'f' * 64, self.root / 'coord',
                                              hostname='trinity-2-28', visible_devices='0', device_uuid=lease['gpu_uuid'], now=now)
        self.assertEqual(result['gpu_uuid'], lease['gpu_uuid'])
        with self.assertRaises(ValueError):
            contracts.authenticate_lease(lease_path, work, 'f' * 64, self.root / 'coord',
                                          hostname='trinity-2-28', visible_devices='0', device_uuid='GPU-wrong', now=now)
        with self.assertRaises(ValueError):
            contracts.authenticate_lease(lease_path, work, 'e' * 64, self.root / 'coord',
                                          hostname='trinity-2-28', visible_devices='0', device_uuid=lease['gpu_uuid'], now=now)

    def test_invalid_gpu_admission_refuses_before_loading_weights(self):
        preflight = load_json(self.checks[contracts.BENCHMARKS[0], 'onethinker'])
        preflight.update(status='CPU_READY', synthetic=False)
        path = self.root / 'preflight.json'
        write_json(path, preflight, self.root)
        lease = self.root / 'invalid_lease.json'
        write_json(lease, {'host': 'wrong-host'}, self.root)
        with mock.patch.object(generate, 'load_local_model') as loader, self.assertRaises(ValueError):
            generate.generate_run(self.manifest(), 'onethinker', 'base', self.root / 'run', self.root, path,
                                  lease_path=lease, coord_root=self.root / 'coord', model_root=self.root / 'models')
        loader.assert_not_called()

    def test_export_bank_is_complete_immutable_and_unregistered(self):
        self.run_fake()
        result = score.score_run(self.root / 'run', self.prepared[contracts.BENCHMARKS[0]] / 'scoring/manifest.json',
                                 self.root / 'score', self.root)
        bank = score.export_bank(self.root / 'run', self.root / 'score/scores.json', 'synthetic-bank', self.root / 'bank', self.root)
        self.assertEqual(bank['shared_registry_status'], 'pending')
        self.assertFalse(bank['publication_ready'])
        archived = load_json(self.root / 'bank/SHA256_MANIFEST.json')
        for relative, expected in archived.items():
            binding(self.root / 'bank' / relative, expected)
        self.assertEqual(sum(name.startswith('run/questions/') for name in archived), 3)
        self.assertIn('run/attempts.jsonl', archived)
        self.assertIn('run/generations.jsonl', archived)
        self.assertIn('scoring/labels.jsonl', archived)
        self.assertIn('preflight/input_audits.jsonl', archived)
        self.assertTrue(any(name.endswith('.png') for name in archived))
        self.assertEqual(result['expected_count'], bank['expected_count'])
        with self.assertRaises((ValueError, FileExistsError)):
            score.export_bank(self.root / 'run', self.root / 'score/scores.json', 'synthetic-bank', self.root / 'bank', self.root)


if __name__ == '__main__':
    unittest.main()
