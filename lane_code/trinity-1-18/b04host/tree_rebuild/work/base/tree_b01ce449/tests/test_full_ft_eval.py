"""The orchard evaluator for full fine-tuned students: full-weights and frozen-VLM publications, the geometry eval
store, camera carriers, and byte-identical identities for the base and LoRA arms against the df6cf8c evaluator."""
import copy
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest import mock

import torch
import transformers

from student_pilot import auxiliary_losses, camera_targets, full_ft, geometry_input
from student_pilot.common import canonical_bytes, load_json
from student_pilot.orchard_eval import contracts, frames, generate
from tests.fullft_eval_toys import (ALL, CAMERA, LABEL, CarrierTokenizer, PublicationFixtures, fixture_frames,
                                    generation_manifest, geometry_settings, rewrite_census, scoring_manifest, tiny_batch,
                                    write_store)
from tests.fullft_toys import tiny_base

REFERENCE = Path(os.environ.get('FULLFT_EVAL_REFERENCE_TREE', '/scratch/jjyeung/pd_build2/trainer'))
REPO = Path(__file__).resolve().parents[1]
SCOPE = {'provisional_diagnostic': LABEL}

# Runs the unmodified evaluator (df6cf8c) on the same fixture files: base and LoRA arms, preflight then mock generation.
REFERENCE_PROGRAM = r'''
import json, sys
tree, request = sys.argv[1], json.loads(sys.argv[2])
sys.path.insert(0, tree)
import pathlib
import student_pilot
assert student_pilot.__file__.startswith(tree), student_pilot.__file__
from student_pilot import orchard_paths
orchard_paths.PROJECT = pathlib.Path(request["project"])
from student_pilot.orchard_eval import frames, generate
root, manifest, label = request["root"], request["manifest"], request["label"]
frames.cpu_check(manifest, request["model"], root + "/check_base", root, synthetic=True, provisional_diagnostic=label)
generate.generate_run(manifest, request["model"], "base", root + "/run_base", root, root + "/check_base/preflight.json",
                      cpu_mock=True, provisional_diagnostic=label)
frames.cpu_check(manifest, request["model"], root + "/check_lora", root, synthetic=True, variant="distilled",
                 adapter=request["adapter"], training_receipt=request["receipt"], provisional_diagnostic=label)
generate.generate_run(manifest, request["model"], "distilled", root + "/run_lora", root, root + "/check_lora/preflight.json",
                      adapter=request["adapter"], training_receipt=request["receipt"], cpu_mock=True,
                      paired_base_run=root + "/run_base", provisional_diagnostic=label)
from student_pilot.orchard_eval import score
for arm in ("base", "lora"):
    score.score_run(root + "/run_" + arm, request["scoring"], root + "/score_" + arm, root, provisional_diagnostic=label)
print("REFERENCE_OK")
'''


def run_arms(root, manifest, model, adapter, receipt, scoring=None):
    from student_pilot.orchard_eval import score
    root = Path(root)
    frames.cpu_check(manifest, model, root / 'check_base', root, synthetic=True, **SCOPE)
    generate.generate_run(manifest, model, 'base', root / 'run_base', root, root / 'check_base/preflight.json',
                          cpu_mock=True, **SCOPE)
    frames.cpu_check(manifest, model, root / 'check_lora', root, synthetic=True, variant='distilled',
                     adapter=adapter, training_receipt=receipt, **SCOPE)
    generate.generate_run(manifest, model, 'distilled', root / 'run_lora', root, root / 'check_lora/preflight.json',
                          adapter=adapter, training_receipt=receipt, cpu_mock=True, paired_base_run=root / 'run_base', **SCOPE)
    if scoring is not None:
        for arm in ('base', 'lora'):
            score.score_run(root / f'run_{arm}', scoring, root / f'score_{arm}', root, **SCOPE)


SCORE_FIELDS = ('benchmark', 'metric', 'primary_score', 'raw_category_macro', 'category_scores', 'missing_categories',
                'expected_count', 'terminal_count', 'started_count', 'missing_count', 'coverage_complete',
                'native_success_count', 'parse_failures', 'parser_branches', 'cap_count', 'failure_counts')


def runtime_names(pins, tree):
    """Runtime bindings by their path inside the evaluator tree (file bytes differ by design between the trees)."""
    return [str(Path(pin['path']).relative_to(tree)) if Path(pin['path']).is_relative_to(tree) else pin for pin in pins]


def comparable(value, tree):
    value = copy.deepcopy(value)
    value['runtime'] = runtime_names(value['runtime'], tree)
    if 'input_audits' in value:
        value['input_audits'] = {key: value['input_audits'][key] for key in ('sha256', 'size_bytes')}
    return value


def receipts(run):
    rows = [json.loads(line) for line in (Path(run) / 'generations.jsonl').read_text().splitlines()]
    return [{key: item for key, item in row.items() if key not in ('runtime_manifest_sha256', 'latency_seconds')} for row in rows]


def load_tiny(model_name, adapter, base_seed=99, attached=None):
    """load_local_model with the tiny native base standing in for the pinned snapshot (loaded in BF16 as usual)."""
    base = tiny_base(model_name, seed=base_seed)
    architecture = getattr(transformers, contracts.MODEL_PINS[model_name]['architecture'])
    with mock.patch.object(architecture, 'from_pretrained', return_value=base):
        return generate.load_local_model(model_name, {'model': {'snapshot': 'unused'}, 'effective_generation_config': {}},
                                         adapter, attached=attached)


def tiny_generation_config(**changes):
    return transformers.GenerationConfig(**{'max_new_tokens': 3, 'do_sample': False, 'num_beams': 1, 'use_cache': True,
                                            'eos_token_id': 2, 'pad_token_id': 0, **changes})


def capture_prefill(model):
    """Pre-hook on the language model that keeps the inputs_embeds of every call (the prefill is the first)."""
    seen = []
    language = model.get_base_model().model.language_model if hasattr(model, 'get_base_model') else model.model.language_model
    handle = language.register_forward_pre_hook(lambda module, args, kwargs: seen.append(kwargs['inputs_embeds'].detach().clone()),
                                                with_kwargs=True)
    return handle, seen


class UnpairedAdapterTests(PublicationFixtures, unittest.TestCase):
    """--allow-unpaired-adapter (the AWS eval closure's flag): the paired run's core plus comparison_mode, nothing else."""

    def setUp(self):
        self.publication_setup()
        self.manifest, _ = generation_manifest(self.stack, self.root)
        self.adapter, self.receipt = self.lora_publication('onethinker')

    def test_the_flag_maps_to_the_closure_semantics(self):
        run_arms(self.root, self.manifest, 'onethinker', self.adapter, self.receipt)
        # Its own attempt authority: the paired run already holds this cohort's authority under self.root.
        external = self.root / 'external'
        external.mkdir()
        arguments = (self.manifest, 'onethinker', 'distilled', external / 'run_unpaired', external,
                     self.root / 'check_lora/preflight.json')
        options = {'adapter': self.adapter, 'training_receipt': self.receipt, 'cpu_mock': True, **SCOPE}
        with self.assertRaisesRegex(ValueError, 'cold-base pair'):
            generate.generate_run(*arguments, paired_base_run=self.root / 'run_base', allow_unpaired_adapter=True, **options)
        with self.assertRaisesRegex(ValueError, 'requires --base-run'):
            generate.generate_run(*arguments, **options)
        generate.generate_run(*arguments, allow_unpaired_adapter=True, **options)
        paired, unpaired = (load_json(path / 'run.json')['core'] for path in (self.root / 'run_lora', external / 'run_unpaired'))
        self.assertEqual(unpaired, {**paired, 'comparison_mode': 'external_parent'})
        strip = lambda rows: [{k: v for k, v in row.items() if k != 'runtime_manifest_sha256'} for row in rows]  # noqa: E731
        self.assertEqual(strip(receipts(external / 'run_unpaired')), strip(receipts(self.root / 'run_lora')))
        from student_pilot.orchard_eval.__main__ import main
        shared = ['--manifest', 'm.json', '--model', 'qwen35', '--output', 'unused/run', '--variant', 'distilled',
                  '--artifact-root', 'unused', '--preflight', 'p.json']
        with mock.patch.object(generate, 'generate_run', return_value={}) as run, redirect_stdout(io.StringIO()):
            main(['generate', *shared, '--allow-unpaired-adapter'])
            self.assertTrue(run.call_args.kwargs['allow_unpaired_adapter'])
            main(['generate', *shared])
            self.assertNotIn('allow_unpaired_adapter', run.call_args.kwargs)


WRAPPER = REPO / 'scripts/orchard/eval_job.py'
# eval_job.py stages inputs under this fixed node-local root; the test pre-stages a uniquely named archive marker there.
STAGED = Path('/tmp/jjyeung/orchard_eval_inputs')
ARCHIVE = 'fullft_wrapper_test_bench.tar'


def wrapper_commands(path, argv, root, extra_env=None):
    """scripts/orchard/eval_job.py main() from `path` with every external effect mocked: its commands, normalized."""
    import importlib.util
    import re
    import uuid
    spec = importlib.util.spec_from_file_location('eval_job_' + uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls, orch = [], Path(root) / ('orch_' + uuid.uuid4().hex[:8])

    def run(*args, env=None):
        args = [str(arg) for arg in args]
        calls.append(args)
        if 'cpu-check' in args:
            output = Path(args[args.index('--output') + 1])
            output.mkdir(parents=True)
            (output / 'preflight.json').write_text(json.dumps({'status': 'CPU_READY', 'failures': [], 'work_id': 'a' * 64,
                                                               'protocol_sha256': 'b' * 64}))

    def check_output(command, text=True):
        return 'c' * 40 + '\n' if 'rev-parse' in command else ''

    env = {'ORCH': str(orch), 'TRAINER': str(root), 'TRAINER_COMMIT': 'c' * 40, 'BENCHMARK_ARCHIVE': str(Path(root) / ARCHIVE),
           'ORCHARD_MEDIA_ATTESTATION_SHA256': 'd' * 64, 'SLURM_JOB_ID': '77', 'STUDENT_MODEL_ROOT': str(Path(root) / 'models'),
           'AGENT_COORD_DIR': str(Path(root) / 'coord'), 'EVAL_SHARD_INDEX': '0', 'EVAL_SHARD_COUNT': '16', **(extra_env or {})}
    with ExitStack() as stack:
        stack.enter_context(mock.patch.dict(os.environ, env))
        for key in ('EVAL_CARRIERS', 'EVAL_GEOMETRY_STORE', 'EVAL_GEOMETRY_STORE_SHA256', 'EVAL_THINKING', 'EVAL_ITEMS_FILE'):
            if key not in env:
                os.environ.pop(key, None)
        stack.enter_context(mock.patch.object(module, 'run', run))
        stack.enter_context(mock.patch.object(module.subprocess, 'check_output', check_output))
        stack.enter_context(mock.patch.object(module.os, 'chdir'))
        stack.enter_context(mock.patch.object(sys, 'argv', ['eval_job.py', *argv]))
        stack.enter_context(mock.patch('student_pilot.orchard_admission.allocation', return_value={'gpu_indices': [0]}))
        stack.enter_context(mock.patch('student_pilot.orchard_admission.issue', return_value=[Path(root) / 'lease.json']))
        stack.enter_context(mock.patch('student_pilot.provisional.bind_lease', return_value={'gpu_uuid': 'GPU-0'}))
        module.main()
    here, identity = str(Path(path).resolve().parent), load_json(orch / 'runs/eval' / argv[3] / 'identity.json')
    text = json.dumps(calls).replace(here, '<HERE>').replace(str(orch), '<ORCH>')
    return json.loads(re.sub(r'lease-77-0-[0-9]+', 'lease-77-0-T', text)), identity


@unittest.skipUnless((REFERENCE / 'scripts/orchard/eval_job.py').is_file(), 'needs the df6cf8c evaluator tree')
class WrapperTests(unittest.TestCase):
    """eval_job.py passes --carriers and the geometry store for head arms; every other cell keeps df6cf8c's commands."""

    def setUp(self):
        import tempfile
        self.root = Path(tempfile.mkdtemp(prefix='eval_wrapper_', dir=os.environ['LANE_TEST_OUTPUT']))
        (self.root / (ARCHIVE + '.sha256')).write_text('e' * 64)
        STAGED.mkdir(parents=True, exist_ok=True)
        (STAGED / (Path(ARCHIVE).stem + '.staged')).write_text('e' * 64)  # staged: no unpack command

    def test_non_head_cells_keep_the_df6cf8c_commands(self):
        for argv in (['prep', 'qwen35', 'base', 'fullftwrapperbase'],
                     ['prep', 'qwen35', 'distilled', 'fullftwrapperlora', 'adapter', 'receipt', 'base_run']):
            with self.subTest(argv=argv):
                ours, our_identity = wrapper_commands(WRAPPER, argv, self.root)
                theirs, their_identity = wrapper_commands(REFERENCE / 'scripts/orchard/eval_job.py', argv, self.root)
                self.assertEqual(ours, theirs)
                self.assertEqual(our_identity, their_identity)
                self.assertEqual([call[call.index('-m') + 2] if '-m' in call else 'stage' for call in ours],
                                 ['stage', 'cpu-check', 'generate'])

    def test_head_cells_pass_carriers_and_the_store(self):
        argv = ['prep', 'qwen35', 'distilled', 'fullftwrapperplain', 'adapter', 'receipt', 'base_run']
        plain, _ = wrapper_commands(WRAPPER, argv, self.root)
        for cell, env, extra in (
                ('fullftwrappercpd', {'EVAL_CARRIERS': 'none'}, ['--carriers', 'none']),
                ('fullftwrapperpdg', {'EVAL_CARRIERS': 'insert', 'EVAL_GEOMETRY_STORE': '/s/manifest.jsonl',
                                      'EVAL_GEOMETRY_STORE_SHA256': 'f' * 64},
                 ['--carriers', 'insert', '--geometry-store-manifest', '/s/manifest.jsonl', '--geometry-store-sha256', 'f' * 64])):
            with self.subTest(cell=cell):
                commands, identity = wrapper_commands(WRAPPER, [*argv[:3], cell, *argv[4:]], self.root, env)
                self.assertEqual(identity['model_args'], extra)
                for ours, before in zip(commands[1:], plain[1:]):
                    before = [item.replace('fullftwrapperplain', cell) for item in before]
                    position = before.index('--provisional-diagnostic') + 2
                    self.assertEqual(ours, before[:position] + extra + before[position:])
        for env in ({'EVAL_CARRIERS': 'always'}, {'EVAL_GEOMETRY_STORE': '/s/manifest.jsonl'}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                wrapper_commands(WRAPPER, argv, self.root, env)
        with self.assertRaisesRegex(ValueError, 'only to distilled'):
            wrapper_commands(WRAPPER, ['prep', 'qwen35', 'base', 'fullftwrapperbase'], self.root, {'EVAL_CARRIERS': 'insert'})


@unittest.skipUnless((REFERENCE / 'student_pilot/orchard_eval/contracts.py').is_file(), 'needs the df6cf8c evaluator tree')
class ParityTests(PublicationFixtures, unittest.TestCase):
    """(a) The base and LoRA arms keep byte-identical audits, identities, work ids, run cores and receipts."""

    def setUp(self):
        self.publication_setup()
        self.manifest, _ = generation_manifest(self.stack, self.root)
        self.adapter, self.receipt = self.lora_publication('onethinker')

    def test_base_and_lora_arms_match_the_df6cf8c_evaluator(self):
        new, reference = self.root / 'new', self.root / 'reference'
        scoring = scoring_manifest(self.root, self.manifest)
        run_arms(new, self.manifest, 'onethinker', self.adapter, self.receipt, scoring)
        reference.mkdir()
        request = {'root': str(reference), 'project': str(self.root), 'manifest': str(self.manifest), 'model': 'onethinker', 'label': LABEL,
                   'adapter': str(self.adapter), 'receipt': str(self.receipt), 'scoring': str(scoring)}
        result = subprocess.run([sys.executable, '-I', '-B', '-c', REFERENCE_PROGRAM, str(REFERENCE), json.dumps(request)],
                                cwd=str(REFERENCE), env=dict(os.environ), capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr[-4000:])
        self.assertIn('REFERENCE_OK', result.stdout)
        for arm in ('base', 'lora'):
            with self.subTest(arm=arm):
                ours, theirs = (load_json(root / f'check_{arm}/preflight.json') for root in (new, reference))
                self.assertEqual((new / f'check_{arm}/input_audits.jsonl').read_bytes(),
                                 (reference / f'check_{arm}/input_audits.jsonl').read_bytes())
                self.assertEqual(ours['protocol_sha256'], theirs['protocol_sha256'])
                self.assertEqual(ours['work_id'], theirs['work_id'])
                self.assertEqual(canonical_bytes(comparable(ours, REPO)), canonical_bytes(comparable(theirs, REFERENCE)))
                core, reference_core = (load_json(root / f'run_{arm}/run.json')['core'] for root in (new, reference))
                self.assertEqual(canonical_bytes(comparable(core, REPO)), canonical_bytes(comparable(reference_core, REFERENCE)))
                self.assertEqual(receipts(new / f'run_{arm}'), receipts(reference / f'run_{arm}'))
                # The scores are byte-identical too.
                ours, theirs = (load_json(root / f'score_{arm}/scores.json') for root in (new, reference))
                self.assertEqual({key: ours[key] for key in SCORE_FIELDS}, {key: theirs[key] for key in SCORE_FIELDS})
                for name in ('per_question_scores.jsonl', 'results.csv', 'compatibility_projection.jsonl'):
                    self.assertEqual((new / f'score_{arm}' / name).read_bytes(), (reference / f'score_{arm}' / name).read_bytes())
                self.assertEqual(ours['terminal_count'], 2)
        lora = load_json(new / 'check_lora/preflight.json')
        self.assertNotIn('carriers', lora)
        self.assertEqual(set(lora['adapter']), {'config', 'weights', 'training_receipt', 'tensor_count'})
        # The scorer re-validates the arm exactly as generation pinned it.
        self.assertEqual(contracts.validate_adapter('distilled', 'onethinker', contracts.adapter_directory_of(lora['adapter']),
                                                    self.receipt, contracts.DEFAULT_CONFIG, True, LABEL, carriers='none'),
                         lora['adapter'])


class FullWeightsTests(PublicationFixtures, unittest.TestCase):
    """(b) Full-weights publications are pinned file by file, load exactly over the base, and refuse tampering."""

    def setUp(self):
        self.publication_setup()

    def validate(self, adapter, receipt, **options):
        return contracts.validate_adapter('distilled', 'qwen35', adapter, receipt, contracts.DEFAULT_CONFIG,
                                          allow_synthetic=True, provisional_diagnostic=LABEL, **options)

    def test_pin_covers_the_export_and_the_load_is_exact_without_peft(self):
        adapter, receipt = self.full_publication()
        pin = self.validate(adapter, receipt)
        export = load_json(adapter / full_ft.EXPORT_DIRECTORY / full_ft.EXPORT_MANIFEST)
        self.assertEqual(pin['format'], contracts.FULL_WEIGHTS_FORMAT)
        self.assertGreater(len(export['files']), 1)
        self.assertEqual([item['sha256'] for item in pin['full_weights']['files']], [item['sha256'] for item in export['files']])
        self.assertEqual(pin['full_weights']['manifest']['sha256'], load_json(receipt)['adapter']['full_weights_manifest_sha256'])
        self.assertEqual(pin['full_weights']['tensor_count'], export['tensor_count'])
        self.assertNotIn('auxiliary_heads', pin)
        self.assertNotIn('carriers', pin)
        self.assertEqual(self.validate(adapter, receipt, carriers='none'), pin)
        attached = {}
        model = load_tiny('qwen35', pin, attached=attached)
        self.assertTrue(attached['full_weights']['full_weights_exact_equality'])
        self.assertEqual(attached['full_weights']['tensors'], export['tensor_count'])
        self.assertFalse(any('lora_' in name for name, _ in model.named_parameters()))
        self.assertFalse(any(parameter.requires_grad for parameter in model.parameters()))
        trained = tiny_base('qwen35', dtype=torch.float32, seed=5)
        expected = {name: parameter.detach().to(torch.bfloat16) for name, parameter in trained.named_parameters()}
        live = dict(model.named_parameters())
        self.assertEqual(set(live), set(expected))
        for name, parameter in live.items():
            self.assertEqual(parameter.dtype, torch.bfloat16, name)
            self.assertTrue(torch.equal(parameter, expected[name]), name)
        untrained = tiny_base('qwen35', seed=99).state_dict()
        self.assertFalse(all(torch.equal(parameter, untrained[name]) for name, parameter in live.items()))
        identity = contracts.adapter_identity(pin)
        self.assertEqual(identity, contracts.digest({'format': pin['format'], 'auxiliary_heads': None,
                                                     'full_weights_manifest': pin['full_weights']['manifest']['sha256']}))

    def test_tampered_shard_index_or_manifest_refuses(self):
        adapter, receipt = self.full_publication()
        pin = self.validate(adapter, receipt)
        folder = adapter / full_ft.EXPORT_DIRECTORY
        shard = folder / load_json(folder / full_ft.EXPORT_MANIFEST)['files'][1]['name']
        original = shard.read_bytes()
        shard.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        with self.assertRaises(ValueError):
            self.validate(adapter, receipt)
        with self.assertRaisesRegex(ValueError, 'differs from its manifest'):
            load_tiny('qwen35', pin)
        shard.write_bytes(original)
        self.assertEqual(self.validate(adapter, receipt), pin)
        index = folder / 'model.safetensors.index.json'
        saved = index.read_bytes()
        index.write_bytes(saved.replace(b'"metadata"', b'"metadata" '))
        with self.assertRaises(ValueError):
            self.validate(adapter, receipt)
        index.write_bytes(saved)
        manifest = folder / full_ft.EXPORT_MANIFEST
        saved = manifest.read_bytes()
        manifest.write_bytes(saved + b'\n')
        with self.assertRaises(ValueError):
            self.validate(adapter, receipt)
        with self.assertRaises(ValueError):
            load_tiny('qwen35', pin)

    def test_mixtures_and_receipt_mismatches_refuse(self):
        adapter, receipt = self.full_publication()
        publish, value = receipt.parent, load_json(receipt)
        cases = {'manifest_sha': {**value, 'adapter': {'full_weights_manifest_sha256': '0' * 64}},
                 'lora_receipt': {**value, 'adapter': {'config_sha256': '0' * 64, 'weights_sha256': '1' * 64}},
                 'frozen_receipt': {**value, 'adapter': {'frozen_vlm': True}},
                 'families': {**value, 'trained_module_families': ['vision', 'merger', 'language']}}
        for name, changed in cases.items():
            path = publish / f'PUBLISHED_{name}.json'
            path.write_bytes(canonical_bytes(changed))
            with self.subTest(case=name), self.assertRaises(ValueError):
                self.validate(adapter, path)
        from student_pilot.benchmark_eval import contracts as benchmark
        with self.assertRaisesRegex(ValueError, 'orchard evaluator'):
            benchmark.validate_adapter('distilled', 'qwen35', adapter, receipt, benchmark.DEFAULT_CONFIG, True, LABEL)
        for options in ({'geometry_store': {'manifest': str(receipt), 'manifest_sha256': '0' * 64}}, {'carriers': 'insert'}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.validate(adapter, receipt, **options)
        # A LoRA file published inside the full-weights adapter directory is a mixture.
        extra = adapter / 'adapter_model.safetensors'
        extra.write_bytes(b'not a lora adapter')
        rewrite_census(publish, lambda files: files.update({f'{adapter.name}/adapter_model.safetensors': {
            'sha256': contracts.sha256(extra), 'bytes': extra.stat().st_size}}))
        with self.assertRaisesRegex(ValueError, 'mixes in LoRA'):
            self.validate(adapter, receipt)

    def test_frozen_vlm_publication_pins_base_and_attached_modules(self):
        store = write_store(self.root / 'store', [fixture_frames(0)], (1, 1))
        adapter, receipt = self.full_publication(train={'llm': False}, geometry=geometry_settings(store), camera=CAMERA, carrier=5)
        with self.assertRaisesRegex(ValueError, 'explicit geometry eval store'):
            self.validate(adapter, receipt, carriers='none')
        with self.assertRaisesRegex(ValueError, 'explicit carriers option'):
            self.validate(adapter, receipt, geometry_store=store)
        pin = self.validate(adapter, receipt, geometry_store=store, carriers='none')
        self.assertEqual(pin['format'], contracts.FROZEN_VLM_FORMAT)
        self.assertNotIn('full_weights', pin)
        self.assertEqual(pin['auxiliary_heads']['sha256'], load_json(receipt.parent / 'training_result.json')['auxiliary_heads']['sha256'])
        self.assertEqual(pin['geometry']['store'], store)
        attached = {}
        model = load_tiny('qwen35', pin, attached=attached)
        self.assertNotIn('full_weights', attached)
        base = tiny_base('qwen35', seed=99)
        for name, parameter in dict(model.named_parameters()).items():
            if not name.startswith('geometry_input.'):
                self.assertTrue(torch.equal(parameter, base.state_dict()[name]), name)
        self.assertIs(attached['geometry'], model.geometry_input)


class GeometryTests(PublicationFixtures, unittest.TestCase):
    """(c) Geometry with full weights: the eval store is explicit and one vision forward consumes the features."""

    def setUp(self):
        self.publication_setup()
        self.store = write_store(self.root / 'store', [fixture_frames(0)], (1, 1))
        self.adapter, self.receipt = self.full_publication(geometry=geometry_settings(self.store, geometry_input.CROSS_INJECTION))

    def test_features_are_consumed_by_exactly_one_vision_forward(self):
        pin = contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG, True, LABEL,
                                         geometry_store=self.store)
        attached = {}
        model = load_tiny('qwen35', pin, attached=attached)
        self.assertTrue(attached['full_weights']['full_weights_exact_equality'])
        module = attached['geometry']
        store = contracts.feature_store(pin['geometry'])
        batch = tiny_batch()
        features = store.tokens(fixture_frames(0), batch['video_grid_thw'][0])
        with torch.inference_mode():
            generated = generate.generate_with_inputs(model, batch, tiny_generation_config(), module, features)
        self.assertEqual(module.calls, 1)
        self.assertGreater(generated.shape[1], batch['input_ids'].shape[1])
        with torch.inference_mode(), self.assertRaisesRegex(ValueError, 'without geometry features'):
            model.generate(**batch, generation_config=tiny_generation_config())
        module.clear()
        # Without a KV cache every decode step re-runs the vision tower, which the evaluator refuses.
        with torch.inference_mode(), self.assertRaises(ValueError):
            generate.generate_with_inputs(model, batch, tiny_generation_config(use_cache=False), module, features)
        self.assertIsNone(module._pending)

    def test_store_is_required_pinned_and_checked(self):
        with self.assertRaisesRegex(ValueError, 'explicit geometry eval store'):
            contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG, True, LABEL)
        with self.assertRaises(ValueError):
            contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG, True, LABEL,
                                       geometry_store={**self.store, 'manifest_sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'geometry-input publication'):
            contracts.validate_adapter('base', 'qwen35', None, None, contracts.DEFAULT_CONFIG, geometry_store=self.store)
        pin = contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG, True, LABEL,
                                         geometry_store=self.store)
        other = write_store(self.root / 'other_store', [fixture_frames(0)], (1, 1), seed=9)
        changed = contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG, True,
                                             LABEL, geometry_store=other)
        self.assertNotEqual(contracts.adapter_identity(pin), contracts.adapter_identity(changed))
        row = contracts.check_geometry_row(contracts.feature_store(pin['geometry']),
                                           {'frame_hashes': fixture_frames(0), 'video_grid_thw': [[16, 2, 2]]})
        self.assertEqual(row['shape'], [32, 1, 1, 8])
        with self.assertRaisesRegex(ValueError, 'video grid'):
            contracts.check_geometry_row(contracts.feature_store(pin['geometry']),
                                         {'frame_hashes': fixture_frames(0), 'video_grid_thw': [[16, 4, 4]]})


class CarrierTests(PublicationFixtures, unittest.TestCase):
    """(d) Eval carriers reproduce training's camera tokens exactly; the option is explicit and needs a camera head."""

    def setUp(self):
        self.publication_setup()
        self.adapter, self.receipt = self.full_publication(camera=CAMERA, carrier=5)

    def validate(self, **options):
        return contracts.validate_adapter('distilled', 'qwen35', self.adapter, self.receipt, contracts.DEFAULT_CONFIG,
                                          allow_synthetic=True, provisional_diagnostic=LABEL, **options)

    def test_prefill_embeddings_and_logits_equal_the_training_forward(self):
        pin = self.validate(carriers='insert')
        self.assertEqual(pin['carriers']['token_id'], 5)
        attached = {}
        model = load_tiny('qwen35', pin, attached=attached)
        carriers = attached['carriers']
        tokenizer = CarrierTokenizer(5)
        extended = camera_targets.insert_carriers(tiny_batch(), tokenizer)
        positions = extended.pop('aux_camera_positions')
        self.assertEqual(int((extended['input_ids'] == 5).sum()), 16)
        # Training: the trainer's heads (with the published state) and its embedding hook on a copy of the same weights.
        reference = copy.deepcopy(model)
        heads = auxiliary_losses.attach(reference, None, tokenizer, CAMERA)
        heads.load_state_dict(torch.load(pin['carriers']['auxiliary_heads']['path'], weights_only=True))
        train_handle = auxiliary_losses.camera_inputs(reference, heads, {**extended, 'aux_camera_positions': positions})
        handle, seen_train = capture_prefill(reference)
        with torch.inference_mode():
            train_logits = reference(**extended, use_cache=False).logits
        train_handle.remove()
        handle.remove()
        # Evaluation: the evaluator's prefill hook on the loaded model.
        handle, seen_eval = capture_prefill(model)
        hook, state = generate.carrier_hook(model, carriers, extended['input_ids'], positions[0].tolist())
        with torch.inference_mode():
            eval_logits = model(**extended, use_cache=False).logits
        hook.remove()
        handle.remove()
        self.assertEqual(state['calls'], 1)
        self.assertTrue(torch.equal(seen_eval[0], seen_train[0]))
        self.assertTrue(torch.equal(eval_logits, train_logits))
        expected = heads.camera.tokens.detach()[[0] + [1] * 15].to(torch.bfloat16)
        self.assertTrue(torch.equal(seen_eval[0][0, positions[0]], expected))
        plain = model.get_input_embeddings()(extended['input_ids'])
        self.assertFalse(torch.equal(seen_eval[0][0, positions[0]], plain[0, positions[0]]))
        # The generation path replaces only its prefill and leaves the decode steps untouched.
        handle, seen_generate = capture_prefill(model)
        with torch.inference_mode():
            generated = generate.generate_with_inputs(model, extended, tiny_generation_config(output_logits=True,
                                                                                               return_dict_in_generate=True),
                                                      carriers=carriers, positions=positions[0].tolist())
        handle.remove()
        self.assertTrue(torch.equal(seen_generate[0], seen_train[0]))
        self.assertTrue(all(step.shape[1] == 1 for step in seen_generate[1:]))
        self.assertTrue(torch.equal(generated.logits[0][0].float(), train_logits[0, -1].float()))

    def test_option_is_explicit_and_needs_a_camera_head(self):
        with self.assertRaisesRegex(ValueError, 'explicit carriers option'):
            self.validate()
        none = self.validate(carriers='none')
        insert = self.validate(carriers='insert')
        self.assertNotIn('carriers', none)
        self.assertEqual({key: value for key, value in insert.items() if key != 'carriers'}, none)
        self.assertNotEqual(contracts.adapter_identity(none), contracts.adapter_identity(insert))
        self.assertEqual(none['auxiliary_heads']['sha256'], insert['carriers']['auxiliary_heads']['sha256'])
        with self.assertRaisesRegex(ValueError, 'camera head'):
            contracts.validate_adapter('base', 'qwen35', None, None, contracts.DEFAULT_CONFIG, carriers='insert')
        with self.assertRaisesRegex(ValueError, 'none or insert'):
            self.validate(carriers='always')
        self.root = self.root / 'plain'  # a second pool under the same Orchard-owned project
        self.root.mkdir()
        plain, plain_receipt = self.full_publication(name='plain')
        with self.assertRaisesRegex(ValueError, 'camera head'):
            contracts.validate_adapter('distilled', 'qwen35', plain, plain_receipt, contracts.DEFAULT_CONFIG, True, LABEL,
                                       carriers='insert')
        identity = contracts.protocol_identity({'sha256': 'a' * 64}, {'model': 'fixture'}, None, contracts.DEFAULT_CONFIG)
        self.assertEqual(identity, contracts.protocol_identity({'sha256': 'a' * 64}, {'model': 'fixture'}, None,
                                                               contracts.DEFAULT_CONFIG, carriers='none'))
        self.assertNotEqual(identity, contracts.protocol_identity({'sha256': 'a' * 64}, {'model': 'fixture'}, None,
                                                                  contracts.DEFAULT_CONFIG, carriers='insert'))

    def test_tampered_heads_refuse(self):
        pin = self.validate(carriers='insert')
        path = Path(pin['carriers']['auxiliary_heads']['path'])
        state = torch.load(path, weights_only=True)
        state['camera.tokens'] = state['camera.tokens'] + 1
        buffer = io.BytesIO()
        torch.save(state, buffer)
        path.write_bytes(buffer.getvalue())
        with self.assertRaises(ValueError):
            self.validate(carriers='insert')
        with self.assertRaises(ValueError):
            load_tiny('qwen35', pin)


class EndToEndTests(PublicationFixtures, unittest.TestCase):
    """(e) cpu_mock preflight and generation of full fine-tuning arms, paired with their cold base."""

    def setUp(self):
        self.publication_setup()
        self.manifest, self.frames = generation_manifest(self.stack, self.root)
        frames.cpu_check(self.manifest, 'qwen35', self.root / 'check_base', self.root, synthetic=True, **SCOPE)
        self.base = generate.generate_run(self.manifest, 'qwen35', 'base', self.root / 'run_base', self.root,
                                          self.root / 'check_base/preflight.json', cpu_mock=True, **SCOPE)
        self.base_core = load_json(self.root / 'run_base/run.json')['core']

    def arm(self, name, adapter, receipt, **options):
        report = frames.cpu_check(self.manifest, 'qwen35', self.root / f'check_{name}', self.root, synthetic=True,
                                  variant='distilled', adapter=adapter, training_receipt=receipt, **options, **SCOPE)
        arguments = (self.manifest, 'qwen35', 'distilled', self.root / f'run_{name}', self.root, self.root / f'check_{name}/preflight.json')
        keywords = {'adapter': adapter, 'training_receipt': receipt, 'cpu_mock': True, 'paired_base_run': self.root / 'run_base',
                    **options, **SCOPE}
        completion = generate.generate_run(*arguments, **keywords)
        self.assertEqual(generate.generate_run(*arguments, **keywords, resume=True), completion)
        return report, completion, load_json(self.root / f'run_{name}/run.json')['core']

    def test_full_weights_arm_with_camera_carriers(self):
        adapter, receipt = self.full_publication(camera=CAMERA, carrier=13)
        report, completion, core = self.arm('insert', adapter, receipt, carriers='insert')
        self.assertEqual(completion['terminal_count'], 2)
        self.assertEqual(set(completion['outcomes'].values()), {'ok'})
        self.assertEqual(report['carriers'], 'insert')
        self.assertEqual(core['adapter'], report['adapter'])
        self.assertEqual(core['adapter']['format'], contracts.FULL_WEIGHTS_FORMAT)
        self.assertEqual(core['model_identity']['adapter_manifest_sha256'], contracts.adapter_identity(report['adapter']))
        # Stripping the carriers gives back exactly the cold base's audits.
        self.assertEqual(core['carriers'], {'mode': 'insert', 'paired_input_audits_sha256': self.base_core['input_audits_sha256']})
        base_audits = contracts.load_jsonl(self.root / 'check_base/input_audits.jsonl')
        audits = contracts.load_jsonl(self.root / 'check_insert/input_audits.jsonl')
        for audit, base in zip(audits, base_audits):
            self.assertEqual(audit['prompt_tokens'], base['prompt_tokens'] + 16)
            self.assertEqual(len(audit['carrier_positions']), 16)
            self.assertEqual(audit['carrier_token_id'], 13)
            self.assertEqual(frames.carrier_free_audit(audit), base)
            self.assertEqual(audit['pixel_tensor_sha256'], base['pixel_tensor_sha256'])
        rows = receipts(self.root / 'run_insert')
        self.assertTrue(all(row['carriers'] == 'insert' and row['status'] == 'ok' for row in rows))
        # The same publication without carriers is a different arm with the base's audits.
        _, _, plain = self.arm('none', adapter, receipt, carriers='none')
        self.assertNotIn('carriers', plain)
        self.assertEqual(plain['input_audits_sha256'], self.base_core['input_audits_sha256'])
        self.assertNotEqual(plain['protocol_sha256'], core['protocol_sha256'])
        # Scoring re-validation reproduces the pin; a preflight from the other carrier mode is refused.
        self.assertEqual(contracts.validate_adapter('distilled', 'qwen35', contracts.adapter_directory_of(core['adapter']),
                                                    core['adapter']['training_receipt']['path'], contracts.DEFAULT_CONFIG, True,
                                                    LABEL, carriers='insert'), core['adapter'])
        with self.assertRaises(ValueError):
            generate.generate_run(self.manifest, 'qwen35', 'distilled', self.root / 'run_mismatch', self.root,
                                  self.root / 'check_none/preflight.json', adapter=adapter, training_receipt=receipt,
                                  cpu_mock=True, paired_base_run=self.root / 'run_base', carriers='insert', **SCOPE)
        with self.assertRaisesRegex(ValueError, 'explicit carriers option'):
            frames.cpu_check(self.manifest, 'qwen35', self.root / 'check_implicit', self.root, synthetic=True,
                             variant='distilled', adapter=adapter, training_receipt=receipt, **SCOPE)

    def test_head_arm_scores_with_carriers(self):
        from student_pilot.orchard_eval import score
        adapter, receipt = self.full_publication(camera=CAMERA, carrier=13)
        _, _, core = self.arm('insert', adapter, receipt, carriers='insert')
        scoring = scoring_manifest(self.root, self.manifest)
        result = score.score_run(self.root / 'run_insert', scoring, self.root / 'score_insert', self.root, **SCOPE)
        self.assertEqual(result['run_core']['carriers']['mode'], 'insert')
        self.assertEqual(result['run_core']['adapter']['carriers'], core['adapter']['carriers'])
        self.assertTrue(result['coverage_complete'])
        self.assertEqual(result['terminal_count'], 2)
        self.assertEqual(len(contracts.load_jsonl(result['per_question_scores']['path'])), 2)
        # Scoring re-validates the carriers the run was generated with: changed head bytes refuse.
        heads = Path(core['adapter']['carriers']['auxiliary_heads']['path'])
        heads.chmod(0o644)
        heads.write_bytes(heads.read_bytes() + b'0')
        with self.assertRaises(ValueError):
            score.score_run(self.root / 'run_insert', scoring, self.root / 'score_tampered', self.root, **SCOPE)

    def test_frozen_vlm_arm_with_geometry_store(self):
        store = write_store(self.root / 'store', [self.frames], (2, 2))
        adapter, receipt = self.full_publication(train={'llm': False}, geometry=geometry_settings(store))
        report, completion, core = self.arm('geometry', adapter, receipt, geometry_store=store)
        self.assertEqual(completion['terminal_count'], 2)
        self.assertEqual(core['adapter']['format'], contracts.FROZEN_VLM_FORMAT)
        self.assertEqual(core['adapter']['geometry']['store'], store)
        self.assertEqual(core['input_audits_sha256'], self.base_core['input_audits_sha256'])
        self.assertNotIn('carriers', report)
        missing = write_store(self.root / 'missing_store', [fixture_frames(3)], (2, 2))
        with self.assertRaisesRegex(ValueError, 'CPU preflight failed'):
            frames.cpu_check(self.manifest, 'qwen35', self.root / 'check_missing', self.root, synthetic=True, variant='distilled',
                             adapter=adapter, training_receipt=receipt, geometry_store=missing, **SCOPE)

    def test_cli_forwards_the_store_and_carriers(self):
        from student_pilot.orchard_eval.__main__ import main
        shared = ['--manifest', 'manifest.json', '--model', 'qwen35', '--output', 'unused/run', '--variant', 'distilled',
                  '--adapter', 'adapter', '--training-receipt', 'receipt', '--artifact-root', 'unused',
                  '--geometry-store-manifest', 'store.jsonl', '--geometry-store-sha256', 'a' * 64, '--carriers', 'insert']
        with mock.patch.object(frames, 'cpu_check', return_value={}) as check, redirect_stdout(io.StringIO()):
            self.assertEqual(main(['cpu-check', *shared]), 0)
        with mock.patch.object(generate, 'generate_run', return_value={}) as run, redirect_stdout(io.StringIO()):
            self.assertEqual(main(['generate', *shared, '--preflight', 'preflight.json']), 0)
        for call in (check, run):
            self.assertEqual(call.call_args.kwargs['geometry_store'], {'manifest': 'store.jsonl', 'manifest_sha256': 'a' * 64})
            self.assertEqual(call.call_args.kwargs['carriers'], 'insert')
        with mock.patch.object(frames, 'cpu_check', return_value={}) as check, redirect_stdout(io.StringIO()):
            main(['cpu-check', *shared[:-6]])
        self.assertIsNone(check.call_args.kwargs['geometry_store'])
        self.assertIsNone(check.call_args.kwargs['carriers'])
        with redirect_stdout(io.StringIO()), mock.patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
            main(['cpu-check', *shared[:-4], '--carriers', 'insert'])


if __name__ == '__main__':
    unittest.main()
