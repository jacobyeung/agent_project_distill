"""Native tiny-export parity, bundle admission and retained host-launch fixtures."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_run as c1, full_ft, mdg_runtime as runtime
from student_pilot.p3_provenance import file_pin, load, sha256, write
from tests.test_grounding_features import tiny_clip


def retained():
    root = Path(os.environ.get('LANE_TEST_OUTPUT', 'artifacts'))
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='mdg_runtime_', dir=root))


def processor(root):
    from transformers import PreTrainedTokenizerFast
    return SimpleNamespace(tokenizer=PreTrainedTokenizerFast(tokenizer_file=str(Path(root) / 'tokenizer.json')))


class Runtime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tokenizers import Tokenizer, models
        from transformers import Qwen3_5ForConditionalGeneration
        cls.root = retained()
        base_dir = cls.root / 'original_base'
        template, cls.batch = tiny_clip(frames=2, h=2, w=2)
        config = copy.deepcopy(template.config)
        base = Qwen3_5ForConditionalGeneration(config).to(torch.bfloat16)
        base.save_pretrained(base_dir)
        vocab = {f'w{i}': i for i in range(40)}
        vocab['<|fim_middle|>'] = vocab.pop('w5')
        tokenizer = Tokenizer(models.WordLevel(vocab, unk_token='w0'))
        tokenizer.save(str(base_dir / 'tokenizer.json'))
        cls.manifest = dict(schema='p3-model-input-v1', root=str(base_dir), base_identity='tiny-base',
            files={p.name: sha256(p) for p in base_dir.iterdir() if p.is_file()})
        write(cls.root / 'model.json', cls.manifest)
        cls.native = dict(trace_program_version='3.14',schema='carrier-c1-run-v1', base_identity='tiny-base', training_mode='final',
            frame_layout='duplicate', frame_markers=True, depth_enabled=True, depth_fov_source='pose_head',
            carrier_placement=template.carrier_placement, recipe=template.recipe, streams={},
            camera_overrides={'weight_focal': 2.}, skip_unsupervised_lm=False)
        depth = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3])
        cls.receipt = dict(schema='c1-preparation-v1', camera=template.auxiliary_heads.pose.settings, depth=depth,
            model=file_pin(cls.root / 'model.json'), recipe={'old': True}, streams={},
            **{k: cls.native[k] for k in ('trace_program_version','training_mode', 'frame_layout', 'depth_enabled', 'depth_fov_source',
                                        'carrier_placement', 'skip_unsupervised_lm')})
        write(cls.root / 'receipt.json', cls.receipt)
        cls.native['preparation'] = file_pin(cls.root / 'receipt.json')
        write(cls.root / 'config.json', cls.native)
        cls.effective = runtime._native(cls.native, cls.receipt, cls.manifest)
        with mock.patch.object(c1, 'processor_for', side_effect=processor):
            proc = c1.processor_for_receipt(cls.manifest, cls.effective)
        trained = c1.load_model(cls.manifest, cls.effective, proc)
        from student_pilot.trace_version import bind
        bind(trained,cls.native)
        optimizer = torch.optim.AdamW([p for p in trained.parameters() if p.requires_grad], lr=1e-3)
        trained.train()
        loss = trained.hidden(cls.batch).float().square().mean()
        loss.backward()
        optimizer.step()
        cls.training_loss = float(loss.detach())
        cls.artifact_dir = cls.root / 'export'
        with mock.patch.object(c1.dist, 'get_rank', return_value=0), mock.patch.object(c1.dist, 'barrier'), \
                mock.patch('student_pilot.fsdp_training.publication_state', return_value=trained.state_dict()):
            c1.export(cls.artifact_dir, trained, trained, cls.native, 1)
        cls.artifact_pin = file_pin(cls.artifact_dir / 'artifact.json')
        cls.proc = proc
        cls.official = c1.load_model(cls.manifest, cls.effective, proc)
        c1.load_artifact(cls.official, cls.artifact_pin)
        cls.official.eval().requires_grad_(False)
        cls.bundle = runtime.make_bundle(cls.root / 'bundle', config=cls.root / 'config.json',
            receipt=cls.root / 'receipt.json', model_manifest=cls.root / 'model.json',
            base_dir=base_dir, artifact_dir=cls.artifact_dir)
        cls.sources = dict(config=cls.root / 'config.json', receipt=cls.root / 'receipt.json',
            model_manifest=cls.root / 'model.json', base_dir=base_dir, artifact_dir=cls.artifact_dir)

    def standalone(self, bundle=None, **extra):
        with mock.patch.object(c1, 'processor_for', side_effect=processor), \
                mock.patch.object(c1, 'prepared', side_effect=AssertionError('AWS closure opened')), \
                mock.patch.object(c1, 'load_model', side_effect=AssertionError('Base shards opened')):
            return runtime.load_runtime(dict(bundle=str(bundle or self.bundle), **extra), 'cpu')

    def test_export_program_version_runs_without_config(self):
        loaded, _, _ = self.standalone()
        self.assertEqual(loaded.trace_program_version,'3.14')
        from student_pilot.trace_format313 import bind_generate, _current
        from tests.test_integ_v314 import Geometry
        @bind_generate
        def generate(model,processor,batch,**kwargs):return _current.get().spec_version
        self.assertEqual(generate(loaded,None,{},ground_backend=SimpleNamespace(geometry=Geometry())),'3.14')

    def test_export_program_version_rejects_mismatched_run_config(self):
        with self.assertRaisesRegex(ValueError,'trace_program_version_mismatch'):
            self.standalone(trace_program_version='3.13')

    def test_native_parameters_buffers_and_prefill_are_bit_identical(self):
        loaded, proc, native = self.standalone(c1_config=str(self.root / 'config.json'), base_artifact=self.artifact_pin)
        self.assertGreater(self.training_loss, 0)
        self.assertEqual(native, self.native)
        self.assertEqual(proc._routing_tokens, self.proc._routing_tokens)
        self.assertTrue(proc.tokenizer._c1_frame_markers)
        expected, actual = self.official.state_dict(), loaded.state_dict()
        self.assertEqual(set(expected), set(actual))
        for name in expected:
            self.assertEqual(expected[name].dtype, actual[name].dtype, name)
            self.assertTrue(torch.equal(expected[name], actual[name]), name)
        expected, actual = dict(self.official.named_buffers()), dict(loaded.named_buffers())
        self.assertEqual(set(expected), set(actual))
        self.assertTrue(any('inv_freq' in name for name in expected))
        for name in expected:
            self.assertEqual(expected[name].dtype, actual[name].dtype, name)
            self.assertTrue(torch.equal(expected[name], actual[name]), name)
        with torch.no_grad():
            self.assertTrue(torch.equal(self.official.hidden(self.batch), loaded.hidden(self.batch)))
        self.assertFalse(loaded.training)
        self.assertFalse(any(p.requires_grad for p in loaded.parameters()))
        self.assertEqual(runtime.tensor_digest(self.official), runtime.tensor_digest(loaded))
        self.assertTrue(loaded.mdg_runtime_report['full_weights_exact_equality'])

    def test_bundle_has_only_small_copies_and_absolute_export_reference(self):
        bundle = load(self.bundle)
        self.assertEqual(bundle['schema'], runtime.SCHEMA)
        self.assertEqual(bundle['artifact_dir'], str(self.artifact_dir))
        self.assertFalse(list(self.bundle.parent.glob('base/*.safetensors')))
        self.assertFalse((self.bundle.parent / 'artifact').exists())
        for name, expected in bundle['files'].items():
            self.assertFalse(Path(name).is_absolute())
            path = (self.artifact_dir / name.removeprefix('artifact/') if name.startswith('artifact/')
                    else self.bundle.parent / name)
            self.assertEqual(sha256(path), expected)
        with self.assertRaises(FileExistsError):
            runtime.make_bundle(self.bundle.parent, **self.sources)

    def test_bundle_tamper_missing_pin_and_path_escape_fail_closed(self):
        for mutation in ('sha', 'missing', 'escape'):
            root = retained()
            target = runtime.make_bundle(root / 'bundle', **self.sources)
            value = load(target)
            if mutation == 'sha':
                (target.parent / 'base/config.json').write_text('{}')
            elif mutation == 'missing':
                value['files'].pop('base/config.json')
            else:
                value['files']['../escape'] = '0' * 64
            target.write_text(json.dumps(value))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.standalone(target)

    def test_identity_and_final_contract_reject_before_model_load(self):
        for field, value in (('frame_layout', 'spread'), ('frame_markers', False), ('depth_enabled', False),
                             ('training_mode', 'mixed'), ('carrier_placement', 'other')):
            native = {**self.native, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                runtime._native(native, self.receipt, self.manifest)
        artifact = load(self.artifact_dir / 'artifact.json')
        for key in ('base_identity', 'config_sha256', 'depth_backing', 'placement', 'training_mode',
                    'frame_layout', 'carrier_position_policy', 'schema', 'pose_backing'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                runtime._artifact({**artifact, key: 'wrong'}, self.native)
        with self.assertRaises(ValueError):
            self.standalone(base_artifact={'path': '/unavailable/aws/artifact.json', 'sha256': '0' * 64})

    def test_export_aws_paths_are_not_dereferenced_and_warm_starts_are_skipped(self):
        root = retained()
        native = {**self.native, 'init_artifact': {'artifact': {'path': '/missing/warm', 'sha256': 'a'*64}},
                  'depth_init': {'path': '/missing/depth', 'sha256': 'b'*64}}
        receipt = {**self.receipt, 'depth_init': native['depth_init']}
        write(root / 'receipt.json', receipt)
        native['preparation'] = file_pin(root / 'receipt.json')
        write(root / 'config.json', native)
        artifact_dir = root / 'export'
        artifact_dir.mkdir()
        artifact = {**load(self.artifact_dir / 'artifact.json'), 'config_sha256': c1.identity(native)}
        for key in ('heads', 'full_weights'):
            artifact[key] = {**artifact[key], 'path': '/unavailable/aws/' + key}
        write(artifact_dir / 'artifact.json', artifact)
        import shutil
        shutil.copyfile(self.artifact_dir / 'heads.pt', artifact_dir / 'heads.pt')
        shutil.copytree(self.artifact_dir / 'full_weights', artifact_dir / 'full_weights')
        bundle = runtime.make_bundle(root / 'bundle', **{**self.sources, 'config': root / 'config.json',
            'receipt': root / 'receipt.json', 'artifact_dir': artifact_dir})
        with mock.patch.object(c1, 'init_from_artifact', side_effect=AssertionError('warm start read')), \
                mock.patch('student_pilot.carrier_c1.load_depth_stage1', side_effect=AssertionError('depth init read')):
            loaded, _, _ = self.standalone(bundle)
        self.assertEqual(set(loaded.mdg_runtime_report['skipped']),
                         {'base_shards', 'base_weight_init', 'init_artifact', 'depth_init'})
        self.assertEqual(runtime.tensor_digest(loaded), runtime.tensor_digest(self.official))

    def test_without_bundle_delegates_to_grounding(self):
        with mock.patch('student_pilot.grounding_train.load_runtime', return_value=('m', 'p', 'c')) as call:
            self.assertEqual(runtime.load_runtime({'a': 1}, 'cpu'), ('m', 'p', 'c'))
        call.assert_called_once_with({'a': 1}, 'cpu')

    def test_cli_writes_parameter_digest_time_and_rss_report(self):
        output = retained() / 'CHECK.json'
        with mock.patch.object(sys, 'argv', ['mdg_runtime', 'check', '--bundle', str(self.bundle),
                                             '--device', 'cpu', '--out', str(output)]), \
                mock.patch.object(c1, 'processor_for', side_effect=processor):
            runtime.main()
        report = load(output)
        self.assertEqual(report['state_sha256'], runtime.tensor_digest(self.official))
        self.assertEqual(report['bundle_sha256'], sha256(self.bundle))
        self.assertEqual(sum(report['group_parameters'].values()), sum(p.numel() for p in self.official.parameters()))
        self.assertGreater(report['group_parameters']['private_depth'], 0)
        self.assertGreater(report['group_parameters']['pose'], 0)
        self.assertGreater(report['load_seconds'], 0)
        self.assertGreater(report['peak_rss_bytes'], 0)

    def test_incomplete_base_or_head_export_cannot_load(self):
        from safetensors.torch import load_file
        for kind in ('base', 'heads'):
            root = retained()
            artifact_dir = root / 'export'
            artifact_dir.mkdir()
            artifact = copy.deepcopy(load(self.artifact_dir / 'artifact.json'))
            manifest, _ = full_ft.read_export(self.artifact_dir / 'full_weights')
            tensors = {}
            for item in manifest['files']:
                tensors.update(load_file(str(self.artifact_dir / 'full_weights' / item['name'])))
            heads = torch.load(self.artifact_dir / 'heads.pt', weights_only=True)
            (tensors if kind == 'base' else heads).pop(next(iter(tensors if kind == 'base' else heads)))
            full_ft.save_export(tensors, artifact_dir / 'full_weights', manifest['base'], manifest['training'])
            torch.save(heads, artifact_dir / 'heads.pt')
            artifact.update(full_weights=file_pin(artifact_dir / 'full_weights/full_weights.json'),
                            heads=file_pin(artifact_dir / 'heads.pt'))
            write(artifact_dir / 'artifact.json', artifact)
            bundle = runtime.make_bundle(root / 'bundle', **{**self.sources, 'artifact_dir': artifact_dir})
            with self.subTest(kind=kind), self.assertRaises((ValueError, RuntimeError)):
                self.standalone(bundle)


class HostLauncher(unittest.TestCase):
    def setUp(self):
        self.root = retained()
        (self.root / 'scripts').mkdir()
        (self.root / 'bin').mkdir()
        (self.root / '.git').mkdir()
        (self.root / '.git/HEAD').write_text('a'*40 + '\n')
        source = Path(__file__).resolve().parents[1] / 'scripts/mdg_host_train.sh'
        self.script = self.root / 'scripts/mdg_host_train.sh'
        self.script.write_text(source.read_text())
        (self.root / 'scripts/mdg_env.sh').write_text(
            f'export MDG_PYTHON={sys.executable}\nexport PATH="{self.root}/bin:$PATH"\n')
        git = self.root / 'bin/git'
        git.write_text('#!/bin/bash\n[[ "$*" == "status --porcelain --untracked-files=all" ]] || exit 9\n[[ -z "${MDG_TEST_GIT_FAIL:-}" ]] || exit 8\nprintf "%s" "${MDG_TEST_DIRTY:-}"\n')
        git.chmod(0o755)
        torchrun = self.root / 'bin/torchrun'
        torchrun.write_text('#!/bin/bash\nprintf "%s\\n" "$*"\n')
        torchrun.chmod(0o755)
        self.config = self.root / 'config.json'
        self.config.write_text('{}\n')
        self.run = self.root / 'run'

    def launch(self, **env):
        return subprocess.run(['bash', str(self.script), str(self.config), '2', str(self.run)],
            env={**os.environ, **env}, capture_output=True, text=True)

    def test_launch_resume_and_changed_config_preserve_receipts_and_log(self):
        self.assertEqual(self.launch().returncode, 0)
        first = (self.run / 'LAUNCH.json').read_bytes()
        log = (self.run / 'train.log').read_bytes()
        receipt = load(self.run / 'LAUNCH.json')
        self.assertEqual(receipt['commit'], 'a'*40)
        self.assertEqual(receipt['config_sha256'], sha256(self.config))
        self.assertIn(b'--standalone --nproc_per_node 2 -m student_pilot.mdg_train train --config', log)
        self.assertEqual(self.launch().returncode, 0)
        self.assertEqual((self.run / 'LAUNCH.json').read_bytes(), first)
        self.assertTrue((self.run / 'LAUNCH_1.json').is_file())
        self.assertEqual((self.run / 'train.log').read_bytes(), log + log)
        self.config.write_text('{"changed": true}')
        self.assertNotEqual(self.launch().returncode, 0)
        self.assertFalse((self.run / 'LAUNCH_2.json').exists())
        self.assertEqual((self.run / 'train.log').read_bytes(), log + log)

    def test_dirty_checkout_rejects_without_launch(self):
        self.assertNotEqual(self.launch(MDG_TEST_DIRTY=' M file').returncode, 0)
        self.assertFalse((self.run / 'LAUNCH.json').exists())

    def test_failed_checkout_probe_rejects_without_launch(self):
        self.assertNotEqual(self.launch(MDG_TEST_GIT_FAIL='1').returncode, 0)
        self.assertFalse((self.run / 'LAUNCH.json').exists())

    def test_sourced_environment_keeps_cuda_and_orders_native_packages_first(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/mdg_env.sh'
        result = subprocess.run(['bash', '-c', 'source "$1"; printf "%s\\n" "$CUDA_VISIBLE_DEVICES" "$PYTHONPATH" "$OMP_NUM_THREADS" "$TRITON_CACHE_DIR"',
                                 'test', str(script)], env={**os.environ, 'CUDA_VISIBLE_DEVICES': '3,4'},
                                capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], '3,4')
        self.assertTrue(lines[1].startswith('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages:/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages'))
        self.assertEqual(lines[2], '4')
        self.assertTrue(lines[3].startswith('/scratch/jjyeung/'))


if __name__ == '__main__':
    unittest.main()
