import io
import os
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from uuid import uuid4

import torch
import transformers

from student_pilot import adapters, ddp_config, orchard_admission as admission, orchard_paths as paths, provisional, students
from student_pilot.orchard_eval import contracts, frames, generate
from student_pilot.orchard_eval.__main__ import main


MODEL = 'qwen36_27b'
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


class TinyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.config = transformers.PretrainedConfig()
        self.config.model_type = 'qwen3_5'
        self.config.use_cache = False
        self.config.text_config = SimpleNamespace(num_hidden_layers=1, hidden_size=4,
                                                 layer_types=['full_attention'], use_cache=False)
        self.config.vision_config = SimpleNamespace(depth=1, deepstack_visual_indexes=[])
        self.name_or_path = 'synthetic-tiny-model'
        self.model = torch.nn.Module()
        self.model.language_model = torch.nn.Module()
        layer = torch.nn.Module()
        for part, names in (('self_attn', ('q_proj', 'k_proj', 'v_proj', 'o_proj')),
                            ('mlp', ('gate_proj', 'up_proj', 'down_proj'))):
            module = torch.nn.Module()
            for name in names:
                module.add_module(name, torch.nn.Linear(4, 4, bias=False))
            layer.add_module(part, module)
        self.model.language_model.layers = torch.nn.ModuleList([layer])
        self.model.visual = torch.nn.Module()
        block = torch.nn.Module()
        for part, names in (('attn', ('qkv', 'proj')), ('mlp', ('linear_fc1', 'linear_fc2'))):
            module = torch.nn.Module()
            for name in names:
                module.add_module(name, torch.nn.Linear(4, 4, bias=False))
            block.add_module(part, module)
        self.model.visual.blocks = torch.nn.ModuleList([block])
        self.model.visual.merger = torch.nn.Module()
        for name in ('linear_fc1', 'linear_fc2'):
            self.model.visual.merger.add_module(name, torch.nn.Linear(4, 4, bias=False))
        self.unrelated = torch.nn.Parameter(torch.tensor([3.0, 7.0]))

    def prepare_inputs_for_generation(self, *args, **kwargs):
        return kwargs


def preflight_model(snapshot='unused-snapshot'):
    return {'model': {'snapshot': snapshot}, 'effective_generation_config': {}}


class RegistryAndDeviceTests(unittest.TestCase):
    def test_model_registry_matches_student_and_frozen_registry(self):
        spec, pin = students.get_student(MODEL), contracts.MODEL_PINS[MODEL]
        self.assertEqual(pin['repo_id'], 'Qwen/Qwen3.6-27B')
        for name in ('architecture', 'revision', 'config_sha256'):
            self.assertEqual(pin[name], spec[name])
        self.assertIs(pin['enable_thinking'], True)
        self.assertEqual(pin['template_sha256'], 'e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259')
        self.assertEqual(set(pin), set(contracts.MODEL_PINS['qwen35']))
        self.assertEqual(contracts.DEFAULT_CONFIG['models'],
                         {name: contracts.MODEL_PINS[name] for name in ('onethinker', 'qwen35')})

    def test_cli_preserves_orchard_controls_and_forwards_loading_options(self):
        shared = ['--manifest', 'manifest.json', '--model', MODEL, '--output', 'unused/run',
                  '--variant', 'distilled', '--checkpoint-dir', 'checkpoints/step_1',
                  '--thinking', 'off', '--max-new-tokens', '128', '--items-file', 'items.json',
                  '--allow-distilled-controls', '--artifact-root', 'unused']
        with mock.patch.object(frames, 'cpu_check', return_value={}) as check, redirect_stdout(io.StringIO()):
            self.assertEqual(main(['cpu-check', *shared]), 0)
        self.assertEqual(check.call_args.args[1], MODEL)
        self.assertEqual(check.call_args.kwargs['checkpoint_dir'], 'checkpoints/step_1')
        for mode in (None, 'single', 'sharded'):
            extra = [] if mode is None else ['--device-mode', mode]
            with self.subTest(mode=mode), mock.patch.object(generate, 'generate_run', return_value={}) as run, redirect_stdout(io.StringIO()):
                self.assertEqual(main(['generate', *shared, '--preflight', 'preflight.json', '--coord-root', 'coord',
                                       '--shard-index', '1', '--shard-count', '2', '--shard-manifest', 'shard.json', *extra]), 0)
            self.assertEqual(run.call_args.kwargs['device_mode'], mode or 'single')
            self.assertEqual(run.call_args.kwargs['checkpoint_dir'], 'checkpoints/step_1')
            self.assertEqual(run.call_args.kwargs['shard_index'], 1)
            self.assertEqual(run.call_args.kwargs['shard_count'], 2)
            self.assertEqual(run.call_args.kwargs['shard_manifest'], 'shard.json')
            self.assertEqual(run.call_args.kwargs['thinking'], 'off')
            self.assertEqual(run.call_args.kwargs['max_new_tokens'], 128)
            self.assertEqual(run.call_args.kwargs['items_file'], 'items.json')
            self.assertIs(run.call_args.kwargs['allow_distilled_controls'], True)
            self.assertEqual(run.call_args.args[7], 'coord')

    def load(self, model=MODEL, mode='single', memory=(80_000_000_000,), visible='0'):
        base = TinyModel()
        with ExitStack() as stack:
            factory = stack.enter_context(mock.patch.object(getattr(transformers, students.get_student(model)['architecture']),
                                                             'from_pretrained', return_value=base))
            stack.enter_context(mock.patch.object(base, 'to', side_effect=AssertionError('Post-load transfer is forbidden')))
            stack.enter_context(mock.patch.dict(os.environ, CUDA_VISIBLE_DEVICES=visible))
            stack.enter_context(mock.patch.object(torch.cuda, 'is_available', return_value=bool(memory)))
            stack.enter_context(mock.patch.object(torch.cuda, 'device_count', return_value=len(memory)))
            props = stack.enter_context(mock.patch.object(torch.cuda, 'get_device_properties',
                                      side_effect=lambda index: SimpleNamespace(total_memory=memory[index])))
            result = generate.load_local_model(model, preflight_model(), None, device_mode=mode)
            return result, factory.call_args, props.call_args_list

    def test_single_device_map_and_freezing(self):
        model, call, _ = self.load()
        self.assertEqual(call.kwargs['device_map'], {'': 'cuda:0'})
        self.assertTrue(call.kwargs['local_files_only'])
        self.assertFalse(call.kwargs['trust_remote_code'])
        self.assertEqual(call.kwargs['dtype'], torch.bfloat16)
        self.assertEqual(call.kwargs['attn_implementation'], 'sdpa')
        self.assertIsInstance(call.kwargs['generation_config'], transformers.GenerationConfig)
        self.assertFalse(model.training)
        self.assertTrue(model.config.use_cache)
        self.assertTrue(model.config.text_config.use_cache)
        self.assertTrue(all(not parameter.requires_grad for parameter in model.parameters()))

    def test_single_refuses_less_than_80gb_before_loading(self):
        for memory in ((), (49 * 1024**3,), (79_999_999_999,)):
            with self.subTest(memory=memory), mock.patch.object(transformers.Qwen3_5ForConditionalGeneration, 'from_pretrained') as factory:
                with mock.patch.object(torch.cuda, 'is_available', return_value=bool(memory)), \
                     mock.patch.object(torch.cuda, 'device_count', return_value=len(memory)), \
                     mock.patch.object(torch.cuda, 'get_device_properties', return_value=SimpleNamespace(total_memory=memory[0] if memory else 0)):
                    with self.assertRaisesRegex(ValueError, '80 GB|CUDA'):
                        generate.load_local_model(MODEL, preflight_model(), None)
                factory.assert_not_called()

    def test_sharded_uses_auto_and_checks_every_visible_card(self):
        _, call, properties = self.load(mode='sharded', memory=(47 * 1024**3, 49 * 1024**3, 50 * 1024**3 - 1), visible='2,4,6')
        self.assertEqual(call.kwargs['device_map'], 'auto')
        self.assertEqual(properties, [mock.call(0), mock.call(1), mock.call(2)])

    def test_sharded_rejects_ineligible_cards_and_visibility(self):
        for memory, visible in (((80_000_000_000, 49 * 1024**3), '0,1'),
                                ((49 * 1024**3, 47 * 1024**3 - 1), '0,1'),
                                ((49 * 1024**3, 50 * 1024**3), '0,1'),
                                ((49 * 1024**3,), '0'), ((49 * 1024**3,) * 2, ''),
                                ((49 * 1024**3,) * 2, '0,0'), ((49 * 1024**3,) * 2, '0,1,2'),
                                ((49 * 1024**3,) * 2, '0, ')):
            with self.subTest(memory=memory, visible=visible), self.assertRaises(ValueError):
                self.load(mode='sharded', memory=memory, visible=visible)

    def test_sharded_refuses_cpu_disk_and_meta_offload(self):
        for device in ('cpu', 'disk', 'meta', torch.device('cpu'), torch.device('meta')):
            model = TinyModel()
            model.hf_device_map = {'model': device}
            with self.subTest(device=device), \
                 mock.patch.object(transformers.Qwen3_5ForConditionalGeneration, 'from_pretrained', return_value=model), \
                 mock.patch.object(generate, 'model_device_map', return_value='auto'), \
                 self.assertRaisesRegex(ValueError, 'offload'):
                generate.load_local_model(MODEL, preflight_model(), None, device_mode='sharded')

    def test_existing_students_keep_single_loading_without_memory_gate(self):
        for model in ('onethinker', 'qwen35'):
            with self.subTest(model=model):
                _, call, properties = self.load(model=model, memory=())
                self.assertEqual(call.kwargs['device_map'], {'': 'cuda:0'})
                self.assertEqual(properties, [])
                with self.assertRaisesRegex(ValueError, MODEL):
                    self.load(model=model, mode='sharded', memory=(49 * 1024**3,) * 2, visible='0,1')
        with self.assertRaises(ValueError):
            self.load(mode='invalid')

    def test_device_mode_validation_does_not_probe_cuda_during_cpu_checks(self):
        with mock.patch.object(torch.cuda, 'is_available', side_effect=AssertionError('CUDA probe')):
            self.assertEqual(generate.model_device_map(MODEL, 'single', check_cuda=False), {'': 'cuda:0'})
            self.assertEqual(generate.model_device_map(MODEL, 'sharded', check_cuda=False), 'auto')
            for model, mode in (('qwen35', 'sharded'), (MODEL, 'invalid')):
                with self.subTest(model=model, mode=mode), self.assertRaises(ValueError):
                    generate.model_device_map(model, mode, check_cuda=False)


class ShardedLeaseTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='orchard_sharded_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.project = self.root / 'project'
        self.coord = self.project / 'coord'
        self.indices = (2, 3)
        self.uuids = {index: f'GPU-00000000-0000-0000-0000-{index:012d}' for index in self.indices}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.object(paths, 'PROJECT', self.project))
        self.stack.enter_context(mock.patch.dict(os.environ, STUDENT_ORCHARD='1', CUDA_VISIBLE_DEVICES='2,3',
                                SLURM_JOB_ID='42', SLURM_JOB_GPUS='2,3', SLURM_STEP_ID='batch',
                                AGENT_COORD_DIR=str(self.coord), STUDENT_FRAME_ROOT_MAP=''))
        self.stack.enter_context(mock.patch.object(admission.socket, 'gethostname', return_value='orchard-community-3'))
        self.stack.enter_context(mock.patch.object(admission, 'command', side_effect=self.controller))
        # Orchard's cgroup renumbers allocated physical GPUs to a local 0..N-1 range, so
        # every admission call site (issue/check_host_lease/admission_probe, reviewed fix
        # 386702e) now invokes provisional.gpu_uuid with the cgroup-local index, never the
        # physical Slurm index. Translate through self.indices the same way the
        # torch.cuda.get_device_properties mock below already does.
        self.stack.enter_context(mock.patch.object(provisional, 'gpu_uuid',
                                side_effect=lambda local: self.uuids[self.indices[local]]))
        self.stack.enter_context(mock.patch.object(torch.cuda, 'is_available', return_value=True))
        self.stack.enter_context(mock.patch.object(torch.cuda, 'device_count', return_value=2))
        self.stack.enter_context(mock.patch.object(torch.cuda, 'get_device_properties',
                                side_effect=lambda ordinal: SimpleNamespace(uuid=self.uuids[self.indices[ordinal]])))

    def controller(self, *args):
        if args[:4] == ('scontrol', 'show', 'job', '-d'):
            return f'JobId=42 JobState=RUNNING Account=mt01 UserId=jjyeung({os.getuid()}) NumNodes=1 NodeList=orchard-community-3 Partition=preempt QOS=preempt_qos GRES=gpu:h100:2(IDX:2-3)'
        if args[:3] == ('scontrol', 'show', 'hostnames'):
            return 'orchard-community-3'
        if args[:2] == ('scontrol', 'listpids'):
            return f'PID JOBID STEPID LOCALID GLOBALID\n{os.getpid()} 42 batch 0 0'
        if args[0] == 'nvidia-smi':
            return f'{os.getpid()}, 100'
        raise AssertionError(args)

    def bundle(self, changes=None):
        folder = self.root / uuid4().hex
        self.work = 'fixture_' + folder.name
        ranks = [{'work_id': f'{self.work}_gpu{index}', 'protocol_sha256': 'a' * 64} for index in self.indices]
        sources = admission.issue({'ranks': ranks}, folder / 'supervisor', LABEL)
        pins = []
        for source, rank, index in zip(sources, ranks, self.indices):
            path = folder / f'bound_{index}.json'
            with mock.patch.dict(os.environ, CUDA_VISIBLE_DEVICES=str(index)):
                lease = provisional.bind_lease(source, path, LABEL, rank['work_id'], rank['protocol_sha256'], self.coord)
            if changes and index == self.indices[-1]:
                path.write_bytes(contracts.canonical_bytes({**lease, **changes}))
            pins.append(contracts.binding(path))
        path = folder / 'bundle.json'
        contracts.write_once(path, {'schema': 'student-sharded-eval-leases-v1', 'leases': pins,
                                   **contracts.provisional_flags(LABEL)}, self.root)
        return path

    def authenticate(self, path, **kwargs):
        return contracts.authenticate_sharded_lease(path, self.work, 'a' * 64, self.coord,
                                                    provisional_diagnostic=LABEL, **kwargs)

    def test_each_gpu_uses_orchard_authentication_and_ownership_probe(self):
        path = self.bundle()
        with mock.patch.object(contracts, 'authenticate_lease', wraps=contracts.authenticate_lease) as authenticate, \
             mock.patch.object(admission, 'admission_probe', wraps=admission.admission_probe) as probe:
            result = self.authenticate(path)
        self.assertEqual([item['gpu_index'] for item in result['devices']], [2, 3])
        self.assertEqual(result['cuda_visible_devices'], '2,3')
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '2,3')
        self.assertEqual(authenticate.call_count, 2)
        self.assertEqual(probe.call_count, 2)
        for index, call, device in zip(self.indices, authenticate.call_args_list, result['devices']):
            self.assertEqual(call.args[1:4], (f'{self.work}_gpu{index}', 'a' * 64, self.coord))
            self.assertEqual(call.kwargs, {'fresh': True, 'provisional_diagnostic': LABEL})
            lease = contracts.load_json(contracts.verify_pin(device['supervisor']))
            self.assertEqual(lease['slurm'], admission.allocation())
            self.assertIs(lease['vnice_wrapped'], False)
        visible = ','.join(self.uuids.values())
        with mock.patch.dict(os.environ, CUDA_VISIBLE_DEVICES=visible):
            self.assertEqual(self.authenticate(path)['cuda_visible_devices'], visible)
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], visible)

    def test_bad_bound_identity_fails_closed_and_restores_visibility(self):
        for change in ({'vnice_wrapped': True}, {'owner': 'foreign-owner'}, {'work_id': 'foreign-work'},
                       {'protocol_sha256': 'b' * 64}, {'gpu_uuid': self.uuids[2]},
                       {'host': 'orchard-community-9'}, {'slurm': {}}, {'coordination_root': str(self.root)},
                       {'ownership_checked_at': (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.authenticate(self.bundle(change))
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '2,3')

    def test_live_slurm_owner_account_job_host_qos_and_membership_are_checked(self):
        path = self.bundle()
        for old, new in (('RUNNING', 'COMPLETED'), ('Account=mt01', 'Account=other'),
                         ('jjyeung(', 'someone('), ('JobId=42', 'JobId=43'),
                         ('preempt_qos', 'flame-16gpu_qos'), ('IDX:2-3', 'IDX:0-1')):
            with self.subTest(old=old), \
                 mock.patch.object(admission, 'command', side_effect=lambda *args: self.controller(*args).replace(old, new)), \
                 self.assertRaises(ValueError):
                self.authenticate(path)
        with mock.patch.object(admission.socket, 'gethostname', return_value='foreign-node'), self.assertRaises(ValueError):
            self.authenticate(path)
        with mock.patch.object(admission, 'command', side_effect=lambda *args: '' if args[:2] == ('scontrol', 'listpids') else self.controller(*args)), \
             self.assertRaises(ValueError):
            self.authenticate(path)
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '2,3')

    def test_coordination_and_foreign_compute_processes_are_checked(self):
        path = self.bundle()
        with mock.patch.object(admission, 'command', side_effect=lambda *args: f'{os.getpid()+1}, 100' if args[0] == 'nvidia-smi' else self.controller(*args)), \
             self.assertRaisesRegex(ValueError, 'foreign'):
            self.authenticate(path)
        pin = contracts.load_json(path)['leases'][-1]
        evidence = Path(contracts.load_json(pin['path'])['coordination_lease_evidence'])
        value = contracts.load_json(evidence)
        evidence.write_bytes(contracts.canonical_bytes({**value, 'status': 'complete'}))
        with self.assertRaisesRegex(ValueError, 'not running'):
            self.authenticate(path)
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '2,3')

    def test_unleased_reordered_and_duplicate_visible_devices_are_rejected(self):
        path = self.bundle()
        for visible in ('2', '2,3,4', '3,2', '2,2', '', ','.join(reversed(list(self.uuids.values())))):
            with self.subTest(visible=visible), mock.patch.dict(os.environ, CUDA_VISIBLE_DEVICES=visible), self.assertRaises(ValueError):
                self.authenticate(path)
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '2,3')
        with mock.patch.object(torch.cuda, 'get_device_properties', return_value=SimpleNamespace(uuid=self.uuids[2])), \
             self.assertRaisesRegex(ValueError, 'UUID'):
            self.authenticate(path)
        for count in (0, 1, 3):
            with self.subTest(count=count), mock.patch.object(torch.cuda, 'device_count', return_value=count), self.assertRaisesRegex(ValueError, 'count'):
                self.authenticate(path)

    def test_bundle_schema_hashes_and_explicit_label_are_required(self):
        path = self.bundle()
        with self.assertRaisesRegex(ValueError, 'provisional'):
            contracts.authenticate_sharded_lease(path, self.work, 'a' * 64, self.coord)
        with self.assertRaises(ValueError):
            contracts.authenticate_lease(path, self.work, 'a' * 64, self.coord, provisional_diagnostic=LABEL)
        value = contracts.load_json(path)
        for changes in ({'schema': 'wrong'}, {'leases': []}, {'leases': value['leases'][:1]}, {'leases': 'bad'},
                        {'provisional_diagnostic': 'FREEFORM_CN_DIAGNOSTIC_PENDING_REVIEW'}):
            other = self.root / (uuid4().hex + '.json')
            contracts.write_once(other, {**value, **changes}, self.root)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.authenticate(other)
        Path(value['leases'][0]['path']).write_bytes(b'{}\n')
        with self.assertRaisesRegex(ValueError, 'Hash|hash|binding'):
            self.authenticate(path)

    def test_orchard_opt_in_and_project_coord_root_cannot_be_bypassed(self):
        path = self.bundle()
        for env in ({'STUDENT_ORCHARD': '0'}, {'AGENT_COORD_DIR': str(self.root / 'outside')}):
            with self.subTest(env=env), mock.patch.dict(os.environ, env), self.assertRaisesRegex(ValueError, 'Orchard'):
                self.authenticate(path)
        with self.assertRaises(ValueError):
            contracts.authenticate_sharded_lease(path, self.work, 'a' * 64, self.root,
                                                 provisional_diagnostic=LABEL)

    def test_refresh_reauthenticates_every_lease_without_freshness_override(self):
        path = self.bundle({'ownership_checked_at': (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()})
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.authenticate(path)
        with mock.patch.object(contracts, 'authenticate_lease', wraps=contracts.authenticate_lease) as authenticate:
            self.authenticate(path, fresh=False)
        self.assertEqual([call.kwargs['fresh'] for call in authenticate.call_args_list], [False, False])
        path = self.bundle({'expires_at': (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()})
        with self.assertRaisesRegex(ValueError, 'expired'):
            self.authenticate(path, fresh=False)


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='orchard_checkpoint_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.base = TinyModel()
        targets = adapters.discover_targets(self.base)
        modules = dict(self.base.named_modules())
        spec = {**students.get_student(MODEL), 'text_config': {'num_hidden_layers': 1, 'hidden_size': 4},
                'target_counts': {group: len(names) for group, names in targets.items()},
                'group_parameters': {group: sum(adapters.RANKS[group] * (modules[name].in_features + modules[name].out_features)
                                               for name in names) for group, names in targets.items()}}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.dict(students.STUDENTS, {MODEL: spec}))
        self.stack.enter_context(mock.patch.object(paths, 'PROJECT', self.root / 'project'))
        self.stack.enter_context(mock.patch.dict(os.environ, STUDENT_ORCHARD='1', STUDENT_FRAME_ROOT_MAP='',
                                                STUDENT_MODEL_ROOT=str(self.root / 'project/models'),
                                                AGENT_COORD_DIR=str(self.root / 'project/coord')))
        self.checkpoint = self.root / 'checkpoints/step_1'
        self.checkpoint.mkdir(parents=True)

    def write_json(self, path, value):
        return contracts.write_once(self.root / path, value, self.root)

    def save_weights(self, training=None):
        source, report = (adapters.attach_adapters(TinyModel()) if training is None
                          else adapters.attach_ddp_adapters(TinyModel(), training))
        groups = adapters.trainable_groups(source, report['targets'])
        weights = {name: torch.arange(parameter.numel(), dtype=parameter.dtype).reshape(parameter.shape) / 17 + index
                   for index, (name, parameter) in enumerate(item for group in groups.values() for item in group)}
        torch.save(weights, self.checkpoint / 'adapters.pt')
        return weights

    def metadata(self, training, **changes):
        run = {'schema': 'provisional-ddp-training-run-v2', 'student': MODEL,
               'base': {'revision': students.get_student(MODEL)['revision']}, 'settings': training,
               **contracts.provisional_flags(LABEL), **changes}
        self.write_json('checkpoints/step_1/artifacts/run.json', run)
        files = {name: {'sha256': contracts.binding(self.checkpoint / name)['sha256'],
                        'bytes': (self.checkpoint / name).stat().st_size}
                 for name in ('adapters.pt', 'artifacts/run.json')}
        self.write_json('checkpoints/step_1/checkpoint.json', {'schema': 'student-ddp-checkpoint-v1', 'step': 1, 'files': files})

    def load(self, preflight=None, mode='single'):
        preflight = preflight or preflight_model()
        with mock.patch.object(transformers.Qwen3_5ForConditionalGeneration, 'from_pretrained', return_value=self.base), \
             mock.patch.object(torch.cuda, 'is_available', return_value=True), \
             mock.patch.object(torch.cuda, 'device_count', return_value=1 if mode == 'single' else 2), \
             mock.patch.object(torch.cuda, 'get_device_properties', return_value=SimpleNamespace(total_memory=80_000_000_000 if mode == 'single' else 49 * 1024**3)), \
             mock.patch.dict(os.environ, CUDA_VISIBLE_DEVICES='0' if mode == 'single' else '0,1'):
            return generate.load_local_model(MODEL, preflight, None, device_mode=mode, checkpoint_dir=self.checkpoint)

    def test_raw_checkpoint_restores_exact_live_names_without_touching_base(self):
        weights = self.save_weights()
        before = {name: parameter.detach().clone() for name, parameter in self.base.named_parameters()}
        with mock.patch.object(adapters, 'attach_adapters', wraps=adapters.attach_adapters) as attach, \
             mock.patch.object(torch, 'load', wraps=torch.load) as load:
            model = self.load()
        attach.assert_called_once_with(self.base)
        load.assert_called_once_with(self.checkpoint / 'adapters.pt', map_location='cpu', weights_only=True)
        restored = dict(model.named_parameters())
        for name, value in weights.items():
            self.assertEqual(restored[name].dtype, value.dtype)
            self.assertTrue(torch.equal(restored[name], value), name)
        for name, value in before.items():
            live = 'base_model.model.' + name
            if live not in restored and name.endswith('.weight'):
                live = live.removesuffix('.weight') + '.base_layer.weight'
            self.assertTrue(torch.equal(restored[live], value), name)
        self.assertFalse(model.training)
        self.assertTrue(all(not parameter.requires_grad for parameter in model.parameters()))

    def test_ddp_checkpoint_uses_recorded_rank_and_alpha_in_sharded_mode(self):
        training = ddp_config.normalize_training_config({'world_size': 2, 'lora_rank': 32, 'lora_alpha': 96}, MODEL)
        weights = self.save_weights(training)
        self.metadata(training)
        pin = contracts.validate_checkpoint('distilled', MODEL, self.checkpoint, provisional_diagnostic=LABEL)
        preflight = {**preflight_model(), 'adapter': pin, **contracts.provisional_flags(LABEL)}
        with mock.patch.object(adapters, 'attach_ddp_adapters', wraps=adapters.attach_ddp_adapters) as attach:
            model = self.load(preflight, mode='sharded')
        attach.assert_called_once_with(self.base, training)
        for name, value in weights.items():
            self.assertTrue(torch.equal(dict(model.named_parameters())[name], value), name)
        self.assertTrue(all(module.scaling['default'] == 3 for module in model.modules() if hasattr(module, 'lora_A')))

    def test_raw_checkpoint_rejects_missing_extra_renamed_and_wrong_tensors(self):
        for mutation in ('missing', 'extra', 'prefix', 'shape', 'dtype', 'not_tensor', 'not_dict'):
            with self.subTest(mutation=mutation):
                self.base = TinyModel()
                weights = self.save_weights()
                name = next(iter(weights))
                if mutation == 'missing':
                    weights.pop(name)
                elif mutation == 'extra':
                    weights['base_model.model.unrelated'] = torch.ones(2)
                elif mutation == 'prefix':
                    weights[name.removeprefix('base_model.model.')] = weights.pop(name)
                elif mutation == 'shape':
                    weights[name] = weights[name].flatten()
                elif mutation == 'dtype':
                    weights[name] = weights[name].to(torch.bfloat16)
                elif mutation == 'not_tensor':
                    weights[name] = 'not a tensor'
                else:
                    weights = list(weights.values())
                torch.save(weights, self.checkpoint / 'adapters.pt')
                with self.assertRaisesRegex(ValueError, 'Checkpoint|checkpoint'):
                    self.load()
                self.assertTrue(torch.equal(self.base.unrelated, torch.tensor([3.0, 7.0])))

    def test_raw_checkpoint_requires_exact_tensor_round_trip(self):
        self.save_weights()
        with mock.patch.object(torch, 'equal', return_value=False), self.assertRaisesRegex(ValueError, 'reload exactly'):
            self.load()

    def test_checkpoint_inputs_are_separate_from_published_adapters(self):
        self.save_weights()
        with mock.patch.object(contracts, 'validate_adapter', side_effect=AssertionError('published validator called')):
            pin = contracts.validate_checkpoint('distilled', MODEL, self.checkpoint)
        self.assertEqual(pin['format'], 'trainer-checkpoint-v1')
        self.assertEqual(pin['weights'], contracts.binding(self.checkpoint / 'adapters.pt'))
        for kwargs in ({'adapter': 'published'}, {'training_receipt': 'receipt.json'}, {'paper': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                contracts.validate_checkpoint('distilled', MODEL, self.checkpoint, **kwargs)
        with self.assertRaises(ValueError):
            contracts.validate_checkpoint('base', MODEL, self.checkpoint)
        with self.assertRaises(ValueError):
            generate.load_local_model(MODEL, preflight_model(), {'config': {}}, checkpoint_dir=self.checkpoint)

    def test_checkpoint_changed_after_preflight_is_rejected(self):
        weights = self.save_weights()
        pin = contracts.validate_checkpoint('distilled', MODEL, self.checkpoint)
        weights[next(iter(weights))].add_(1)
        torch.save(weights, self.checkpoint / 'adapters.pt')
        with self.assertRaisesRegex(ValueError, 'preflight|Preflight|binding|changed'):
            self.load({**preflight_model(), 'adapter': pin})

    def test_ddp_metadata_must_match_saved_hashes_and_explicit_label(self):
        training = ddp_config.normalize_training_config({'world_size': 2}, MODEL)
        self.save_weights(training)
        self.metadata(training)
        with self.assertRaises(ValueError):
            contracts.validate_checkpoint('distilled', MODEL, self.checkpoint)
        header = contracts.load_json(self.checkpoint / 'artifacts/run.json')
        header['settings']['lora_alpha'] += 1
        (self.checkpoint / 'artifacts/run.json').write_bytes(contracts.canonical_bytes(header))
        with self.assertRaisesRegex(ValueError, 'Hash|hash|changed'):
            contracts.validate_checkpoint('distilled', MODEL, self.checkpoint, provisional_diagnostic=LABEL)

    def test_ddp_metadata_rejects_wrong_model_revision_and_unnormalized_settings(self):
        training = ddp_config.normalize_training_config({'world_size': 2}, MODEL)
        for changes in ({'student': 'qwen35'}, {'base': {'revision': 'wrong'}}, {'settings': {'world_size': 2}}):
            with self.subTest(changes=changes):
                self.root = Path(tempfile.mkdtemp(prefix='orchard_metadata_', dir=os.environ['LANE_TEST_OUTPUT']))
                self.checkpoint = self.root / 'checkpoints/step_1'
                self.checkpoint.mkdir(parents=True)
                self.save_weights(training)
                self.metadata(training, **changes)
                with self.assertRaisesRegex(ValueError, 'different model|normalized'):
                    contracts.validate_checkpoint('distilled', MODEL, self.checkpoint, provisional_diagnostic=LABEL)

    def generation_manifest(self):
        root = self.root / 'generation'
        video = contracts.write_bytes_once(root / 'video.bin', b'synthetic media fixture', self.root)
        receipt = contracts.write_once(root / 'frame_receipt.json', {'cache_contract': {'video_sha256': video['sha256']}}, self.root)
        rows = [{'qid': f'synthetic-{index}', 'video_id': 'synthetic-video', 'student_input': {
                 'question': 'Synthetic question', 'options': ['A. red', 'B. blue'],
                 'options_serialization': 'A. red\nB. blue', 'video_path': video['path'],
                 'video_sha256': video['sha256'], 'frame_receipt': receipt}} for index in range(3)]
        ids = [row['qid'] for row in rows]
        source = {key: rows[0]['student_input'][key] for key in ('video_path', 'video_sha256', 'frame_receipt')}
        manifest = {'schema': 'student-generation-manifest-v1', 'benchmark': 'vstibench_repr450_v2',
                    'paper_cell': False, 'ordered_ids': ids, 'expected_count': 3, 'preprocessing': contracts.RGB,
                    'cohort_authority_sha256': 'a' * 64, 'guard': None, 'media_roots': [str(root)],
                    'config': contracts.write_once(root / 'config.json', contracts.DEFAULT_CONFIG, self.root),
                    'inputs': contracts.write_bytes_once(root / 'inputs.jsonl', contracts.jsonl_bytes(rows), self.root),
                    'media': contracts.write_once(root / 'media.json', {'synthetic-video': source}, self.root),
                    'membership': contracts.write_once(root / 'membership.json', {'qids': ids}, self.root),
                    'admission_input': contracts.write_once(root / 'admission_input.json', rows, self.root),
                    **contracts.prompt_provenance(contracts.DEFAULT_CONFIG)}
        path = root / 'manifest.json'
        contracts.write_once(path, manifest, self.root)
        attestation = self.write_json('attestation.json', {'schema': 'orchard-prepared-media-attestation-v1', 'manifests': {
            str(path): {'manifest': contracts.binding(path), 'media': manifest['media'], 'videos': {video['path']: source}}}})
        self.stack.enter_context(mock.patch.dict(os.environ, ORCHARD_MEDIA_ATTESTATION=attestation['path'],
                                                ORCHARD_MEDIA_ATTESTATION_SHA256=attestation['sha256']))
        return path

    @staticmethod
    def pack_fixture(processor, row, model, config, thinking='pinned'):
        return {'input_ids': torch.tensor([[1, 2]])}, {'qid': row['qid'], 'prompt_tokens': 2}

    def test_three_row_checkpoint_preflight_generation_and_resume(self):
        weights = self.save_weights()
        manifest = self.generation_manifest()
        with mock.patch.object(frames, 'pack_input', side_effect=self.pack_fixture), \
             mock.patch.object(generate, 'pack_input', side_effect=self.pack_fixture):
            frames.cpu_check(manifest, MODEL, self.root / 'base_check', self.root, synthetic=True)
            generate.generate_run(manifest, MODEL, 'base', self.root / 'base', self.root,
                                  self.root / 'base_check/preflight.json', cpu_mock=True)
            with mock.patch.object(frames, 'validate_adapter', side_effect=AssertionError('published path called')), \
                 mock.patch.object(generate, 'validate_adapter', side_effect=AssertionError('published path called')):
                report = frames.cpu_check(manifest, MODEL, self.root / 'checkpoint_check', self.root, synthetic=True,
                                          variant='distilled', checkpoint_dir=self.checkpoint)
                args = (manifest, MODEL, 'distilled', self.root / 'checkpoint_run', self.root,
                        self.root / 'checkpoint_check/preflight.json')
                options = {'cpu_mock': True, 'checkpoint_dir': self.checkpoint, 'paired_base_run': self.root / 'base'}
                completion = generate.generate_run(*args, **options)
                self.assertEqual(completion['expected_count'], 3)
                self.assertEqual(completion['terminal_count'], 3)
                core = contracts.load_json(self.root / 'checkpoint_run/run.json')['core']
                self.assertEqual(core['adapter'], report['adapter'])
                self.assertEqual(core['device_mode'], 'single')
                self.assertEqual(core['model_identity']['adapter_manifest_sha256'],
                                 contracts.digest({'weights': contracts.binding(self.checkpoint / 'adapters.pt')['sha256']}))
                self.assertEqual(generate.generate_run(*args, **options, resume=True), completion)
                with self.assertRaisesRegex(ValueError, 'settings differ'):
                    generate.generate_run(*args, **options, resume=True, device_mode='sharded')
                weights[next(iter(weights))].add_(1)
                torch.save(weights, self.checkpoint / 'adapters.pt')
                with self.assertRaisesRegex(ValueError, 'Preflight'):
                    generate.generate_run(*args, **options, resume=True)

    def test_checkpoint_preserves_thinking_token_subset_and_manifest_sharding_controls(self):
        self.save_weights()
        manifest = self.generation_manifest()
        items = self.write_json('items.json', ['synthetic-0', 'synthetic-2'])['path']
        controls = {'thinking': 'off', 'max_new_tokens': 128, 'items_file': items, 'allow_distilled_controls': True}
        with mock.patch.object(frames, 'pack_input', side_effect=self.pack_fixture), \
             mock.patch.object(generate, 'pack_input', side_effect=self.pack_fixture):
            for variant in ('base', 'distilled'):
                checkpoint = {'checkpoint_dir': self.checkpoint} if variant == 'distilled' else {}
                check = self.root / (variant + '_check')
                frames.cpu_check(manifest, MODEL, check, self.root, synthetic=True, variant=variant, **checkpoint, **controls)
                args = (manifest, MODEL, variant, self.root / variant, self.root, check / 'preflight.json')
                pair = {'paired_base_run': self.root / 'base'} if variant == 'distilled' else {}
                generate.generate_run(*args, cpu_mock=True, shard_count=2, shard_index=0, **checkpoint, **controls, **pair)
                completion = generate.generate_run(*args, cpu_mock=True, shard_count=2, shard_index=1, **checkpoint, **controls, **pair)
                self.assertEqual(completion['expected_count'], 2)
                self.assertEqual(completion['terminal_count'], 2)
                core = contracts.load_json(self.root / variant / 'run.json')['core']
                self.assertEqual(core['ordered_ids'], ['synthetic-0', 'synthetic-2'])
                self.assertEqual(core['thinking_mode'], 'off')
                self.assertEqual(core['decoding']['max_new_tokens'], 128)

    def test_generate_forwards_checkpoint_and_reauthenticates_all_sharded_call_sites(self):
        self.save_weights()
        manifest = self.generation_manifest()
        scope = {'provisional_diagnostic': LABEL}
        with mock.patch.object(frames, 'pack_input', side_effect=self.pack_fixture), \
             mock.patch.object(generate, 'pack_input', side_effect=self.pack_fixture):
            frames.cpu_check(manifest, MODEL, self.root / 'base_check', self.root, synthetic=True, **scope)
            generate.generate_run(manifest, MODEL, 'base', self.root / 'base', self.root,
                                  self.root / 'base_check/preflight.json', cpu_mock=True, device_mode='sharded', **scope)
            report = frames.cpu_check(manifest, MODEL, self.root / 'checkpoint_check', self.root, synthetic=True,
                                      variant='distilled', checkpoint_dir=self.checkpoint, **scope)
        report.update(status='CPU_READY', synthetic=False)
        report['model']['snapshot'] = 'unused-model-snapshot'
        report['protocol_sha256'] = contracts.protocol_identity(report['manifest'], report['model'], report['adapter'], report['config'], LABEL)
        report['work_id'] = contracts.work_id('vstibench_repr450_v2', MODEL, 'distilled', report['protocol_sha256'])
        self.write_json('gpu_preflight.json', report)
        header = contracts.load_json(self.root / 'base/run.json')
        header['core']['mock'] = False
        header['core']['model_snapshot'] = report['model']
        self.write_json('gpu_base/run.json', header)
        processor = frames.SyntheticProcessor()
        tokens = processor.tokenizer.encode('<answer>A</answer><|im_end|>')
        model = mock.Mock(generation_config=transformers.GenerationConfig.from_dict(report['effective_generation_config']))
        model.generate.return_value = SimpleNamespace(sequences=torch.tensor([[1, 2, *tokens]]))
        cpu_input = mock.Mock()
        cpu_input.to.return_value = torch.tensor([[1, 2]])
        pack = lambda processor, row, *args: ({'input_ids': cpu_input}, {'qid': row['qid'], 'prompt_tokens': 2})
        with mock.patch.object(generate, 'authenticate_sharded_lease', return_value={}) as lease, \
             mock.patch.object(generate, 'authenticate_lease', side_effect=AssertionError('single lease used')), \
             mock.patch.object(admission, 'admitted_eval_device', side_effect=AssertionError('single device used')), \
             mock.patch.object(generate, 'model_device_map', return_value='auto'), \
             mock.patch.object(contracts, 'snapshot_binding', return_value=report['model']), \
             mock.patch.object(transformers, 'set_seed'), \
             mock.patch.object(transformers.AutoProcessor, 'from_pretrained', return_value=processor), \
             mock.patch.object(generate, 'load_local_model', return_value=model) as loader, \
             mock.patch.object(generate, 'pack_input', side_effect=pack), \
             mock.patch.object(torch.cuda, 'reset_peak_memory_stats'), \
             mock.patch.object(torch.cuda, 'max_memory_allocated', return_value=0), \
             mock.patch.object(torch.cuda, 'max_memory_reserved', return_value=0):
            completion = generate.generate_run(manifest, MODEL, 'distilled', self.root / 'gpu_run', self.root,
                                  self.root / 'gpu_preflight.json', lease_path='synthetic-bundle',
                                  coord_root=self.root / 'project/coord', model_root='unused-model-root',
                                  checkpoint_dir=self.checkpoint, device_mode='sharded', paired_base_run=self.root / 'gpu_base', **scope)
        self.assertEqual(completion['terminal_count'], 3)
        self.assertEqual(model.generate.call_count, 3)
        self.assertEqual(lease.call_count, 5)
        self.assertEqual([call.kwargs.get('fresh', True) for call in lease.call_args_list], [True, False, False, False, False])
        self.assertTrue(all(call.args[1] == report['work_id'] for call in lease.call_args_list))
        loader.assert_called_once_with(MODEL, report, None, device_mode='sharded', checkpoint_dir=self.checkpoint)
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    unittest.main()
