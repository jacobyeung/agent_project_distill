import copy
from contextlib import ExitStack, nullcontext
import inspect
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SEALED = ROOT.parent / 'tree_s1_admissionfix_168872'
sys.path.insert(0, str(SEALED))
import student_pilot
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))

import torch
from torch import nn
from student_pilot import carrier_c1_run as run, carrier_c1_data as data, full_ft
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import digest, file_pin, write

torch.set_num_threads(2)
DONOR_TREE = 'b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
TOKENS = {'ids': {'<pose': 5}, 'constituents': {'<pose': [1, 2]}}


class Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(12, 4)
        self.head = nn.Linear(4, 12, bias=False)
        self.auxiliary_heads = nn.Module()
        self.auxiliary_heads.pose = nn.Linear(4, 2)
        self.auxiliary_heads.depth = nn.Linear(4, 1)
        self.auxiliary_heads.frame_embeddings = nn.Embedding(32, 4)
        self.carrier_placement = data.C1_A
        self.frame_layout = 'duplicate'
        self.carrier_position_policy = 'native_v1'
        self.training_mode = 'final'
        self.geometry_online = None

    def get_input_embeddings(self):
        return self.embed

    def get_output_embeddings(self):
        return self.head

    def forward(self, indices):
        values = self.embed(indices)
        return self.head(values).float().square().mean()


def fixture():
    root = Path(tempfile.mkdtemp(prefix='native_export_', dir=ROOT / 'fixtures'))
    donor_cfg = dict(schema='carrier-c1-run-v1', training_mode='final', init='base',
                     parallel='fsdp', all_frames=True, carrier_placement=data.C1_A,
                     frame_layout='duplicate', depth_enabled=True, depth_fov_source='pose_head',
                     steps=1000, milestones=[1, 50, 100, 200, 400, 600, 800, 1000],
                     world_size=4, reference_world_size=4,
                     mix=['pose', 'vqa', 'pointing', 'routing'], gate_stop=False,
                     recipe={'warmup_ratio': .05, 'wall_seconds': 86400, 'stop_before_seconds': 3600},
                     base_identity='tiny-schema-fixture', trace_program_version='3.14',
                     output=str(root / 'runs/469ddece'), preparation_output=str(root / 'donor_prep'))
    donor_cfg['scheduled_sampling'] = dict(depth_open_absrel=.25, ema_steps=100, exposure_from_step=None,
        exposure_probability=0., force_from_step=None, fov_open_deg=2., max_own_probability=0.,
        pose_full_deg=10., pose_open_deg=20., seed=17)
    donor_cfg['recipe'] = recipe_for(donor_cfg)
    write(root / 'parent.json', {'schema': 'carrier-c1-artifact-v1', 'head_init': None})
    donor_cfg['init_artifact'] = dict(artifact=file_pin(root / 'parent.json'), lm='full', heads=['pose', 'depth'])
    stream_data = {}
    donor_cfg['streams'] = {}
    for i, name in enumerate(('pointing', 'pose', 'routing', 'vqa')):
        database = root / (name + '.sqlite')
        with sqlite3.connect(database) as conn:
            conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
            conn.executemany('INSERT INTO rows VALUES (?, ?, ?)', [
                (j, json.dumps({'qid': name + ':' + str(j)}), json.dumps({'value': j}))
                for j in range(19 + i)])
        write(root / (name + '.json'), {'fixture': name})
        pin = file_pin(root / (name + '.json'))
        donor_cfg['streams'][name] = pin
        stream_data[name] = dict(receipt=pin, database=file_pin(database), count=19 + i, source_count=19 + i)
    archive = dict(path=str(root / 'logical_source.tar'), sha256='a' * 64)
    seal = dict(schema='s1-run-seal-v1', tree_sha256=DONOR_TREE,
                config_sha256=run.identity(donor_cfg), archive=archive)
    seal['sha256'] = digest(seal)
    prep = dict(schema='c1-preparation-v1', config_sha256=run.identity(donor_cfg),
                streams=stream_data, recipe=donor_cfg['recipe'], source_seal=seal,
                training_mode='final', camera={}, depth={}, base_identity=donor_cfg['base_identity'],
                carrier_placement=data.C1_A, frame_layout='duplicate', depth_enabled=True,
                depth_fov_source='pose_head', trace_program_version='3.14')
    write(root / 'donor_preparation.json', prep)
    donor_cfg['preparation'] = file_pin(root / 'donor_preparation.json')
    write(root / 'donor_config.json', donor_cfg)
    model = Tiny()
    with torch.no_grad():
        model.embed.weight[5].fill_(7.125)
        model.head.weight[5].fill_(-3.25)
        model.auxiliary_heads.frame_embeddings.weight.fill_(.375)
    export = root / 'm200'
    export.mkdir()
    tensors = {name: value.detach().to(torch.bfloat16).contiguous()
               for name, value in full_ft.base_parameters(model)}
    full_ft.save_export(tensors, export / 'full_weights',
                        {'base_identity': donor_cfg['base_identity']}, {'fixture': True})
    torch.save(model.auxiliary_heads.state_dict(), export / 'heads.pt')
    artifact = dict(schema='carrier-c1-artifact-v1', step=200, config_sha256=run.identity(donor_cfg),
                    base_identity=donor_cfg['base_identity'], placement=data.C1_A,
                    training_mode='final', pose_backing='lm_final_norm', frame_layout='duplicate',
                    carrier_position_policy='native_v1', trace_program_version='3.14',
                    source_seal=seal, training_source_seal=seal,
                    full_weights=file_pin(export / 'full_weights/full_weights.json'),
                    heads=file_pin(export / 'heads.pt'))
    write(export / 'artifact.json', artifact)
    cfg = copy.deepcopy(donor_cfg)
    cfg.update(output=str(root / 'runs/fedcba98'), preparation_output=str(root / 'receiver_prep'),
               init_artifact=dict(artifact=file_pin(export / 'artifact.json'), lm='full',
                                  heads=['pose', 'depth', 'frame_embeddings']),
               warm_start=dict(schema='s1-export-warm-start-v1', donor_config=file_pin(root / 'donor_config.json')))
    receipt = {**prep, 'init_artifact': cfg['init_artifact'],
               'warm_start': {'schema': 's1-export-warm-start-v1', 'step': 200, 'inherited_head_params': []}}
    return root, cfg, donor_cfg, receipt, model


def load_fixture(root, receipt, receiver):
    processor = SimpleNamespace(tokenizer=None, _routing_tokens=copy.deepcopy(TOKENS))
    with patch('transformers.Qwen3_5ForConditionalGeneration.from_pretrained', return_value=None), \
         patch.object(run, 'CarrierC1', return_value=receiver), \
         patch('student_pilot.camera_targets.carrier_id', return_value=5):
        return run.load_model({'root': str(root), 'files': {}}, receipt, processor)


class Regression(unittest.TestCase):
    def test_model_loader_preserves_warmed_routing_rows(self):
        root, cfg, donor, receipt, model = fixture()
        loaded = load_fixture(root, receipt, Tiny())
        torch.testing.assert_close(loaded.embed.weight[5], model.embed.weight[5], rtol=0, atol=0)
        torch.testing.assert_close(loaded.head.weight[5], model.head.weight[5], rtol=0, atol=0)
        for name, value in loaded.auxiliary_heads.state_dict().items():
            torch.testing.assert_close(value, model.auxiliary_heads.state_dict()[name], rtol=0, atol=0)

    def test_first_batch_uses_post_export_plan(self):
        root, cfg, donor, receipt, model = fixture()
        captured = []
        counts = {name: value['count'] for name, value in receipt['streams'].items()}
        expected = next(data.mixed_indices(counts, 201, start_step=200, training_mode='final',
                                           mix=cfg['recipe']['mix'], world=4))
        with patch.object(run, 'prepared', return_value=(receipt, {})), \
             patch.object(run, 'processor_for_receipt', return_value=None), \
             patch.object(run, 'load_model', return_value=model), \
             patch.object(run, 'Rows', return_value=SimpleNamespace(close=lambda: None)), \
             patch.object(run, 'check_plan_rows', side_effect=lambda m, r, p, ranks, **kw: captured.append((p, ranks)) or []):
            run.first_batch_check(cfg, [0, 1, 2, 3], root / 'first_batch.json')
        self.assertEqual(captured, [([expected], [0, 1, 2, 3])])

    def test_without_warm_block_keeps_original_opener_initialization(self):
        root, cfg, donor, receipt, model = fixture()
        receipt.pop('warm_start')
        loaded = load_fixture(root, receipt, Tiny())
        expected = model.embed.weight[[1, 2]].to(torch.bfloat16).float().mean(0)
        torch.testing.assert_close(loaded.embed.weight[5], expected, rtol=0, atol=0)
        self.assertFalse(hasattr(loaded, 'warm_start_lineage'))


class Contract(unittest.TestCase):
    def setUp(self):
        from student_pilot import s1_warm_start
        self.warm = s1_warm_start
        self.root, self.cfg, self.donor, self.receipt, self.model = fixture()

    def variant(self, name, value):
        path = self.root / (name + '.json')
        write(path, value)
        return file_pin(path)

    def artifact(self, **changes):
        value = run.load(self.cfg['init_artifact']['artifact']['path'])
        value.update(changes)
        result = copy.deepcopy(self.cfg)
        result['init_artifact']['artifact'] = self.variant('artifact_' + str(len(list(self.root.iterdir()))), value)
        return result

    def test_binds_native_export_schema_and_builds_all_rank_rows(self):
        lineage = self.warm.bind(self.cfg, self.receipt)
        self.assertEqual(lineage['step'], 200)
        self.assertFalse(lineage['exact_resume'])
        self.assertEqual(lineage['optimizer'], 'fresh_adamw')
        rows = run.Rows(self.receipt, None)
        try:
            plan = next(data.mixed_indices(rows.counts, 201, start_step=200, training_mode='final',
                                           mix=self.cfg['recipe']['mix'], world=4))
            built = [(rank, stream, rows.row(stream, indices[rank])[0]['qid'])
                     for rank in range(4) for stream, indices in plan]
            self.assertEqual(len(built), 16)
            self.assertTrue(all(qid == stream + ':' + str(indices[rank])
                for rank, stream, qid in built for name, indices in plan if name == stream))
            write(self.root / 'first_post_export_rows.json', built)
        finally:
            rows.close()

    def test_native_payload_load_and_fresh_adamw_use_absolute_lr(self):
        lineage = self.warm.bind(self.cfg, self.receipt)
        loaded = load_fixture(self.root, {**self.receipt, 'warm_start': lineage}, Tiny())
        expected = dict(full_ft.base_parameters(self.model))
        for name, value in full_ft.base_parameters(loaded):
            torch.testing.assert_close(value, expected[name].to(torch.bfloat16).float(), rtol=0, atol=0)
        optimizer = torch.optim.AdamW(run.parameter_groups(loaded), weight_decay=.01)
        self.assertEqual(len(optimizer.state), 0)
        for group in optimizer.param_groups:
            group['lr'] = run.learning_rate(201, {**self.cfg['recipe'], 'learning_rate': group['initial_lr']})
            self.assertEqual(group['lr'], run.learning_rate(201, {**self.donor['recipe'],
                                                                   'learning_rate': group['initial_lr']}))
        loss = loaded(torch.tensor([1, 3, 5]))
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        optimizer.step()
        self.assertTrue(all(float(value['step']) == 1 for value in optimizer.state.values()))

    def test_bad_steps_and_manual_offsets_are_refused(self):
        for step in (0, -1, 1000, 1001, True, 1.5, '200'):
            with self.subTest(step=step), self.assertRaisesRegex(ValueError, 'export step'):
                self.warm.bind(self.artifact(step=step), self.receipt)
        bad = copy.deepcopy(self.cfg)
        bad['warm_start']['start_step'] = 200
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.warm.validate(bad)
        with self.assertRaisesRegex(ValueError, 'no row offset'):
            self.warm.validate({**self.cfg, 'row_start_step': 200})

    def test_identity_policy_and_destination_changes_are_refused(self):
        for key, value in (('config_sha256', 'f' * 64), ('base_identity', 'another-base'),
                           ('training_mode', 'pose_only'), ('frame_layout', 'spread')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.warm.bind(self.artifact(**{key: value}), self.receipt)
        for changes in ({'output': self.donor['output']},
                        {'preparation_output': self.donor['preparation_output']},
                        {'lm_lr_scale': .7}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.warm.bind({**self.cfg, **changes}, self.receipt)

    def test_donor_tree_and_metadata_tampering_are_refused(self):
        artifact = run.load(self.cfg['init_artifact']['artifact']['path'])
        bad_seal = {**artifact['source_seal'], 'tree_sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'seal'):
            self.warm.bind(self.artifact(source_seal=bad_seal), self.receipt)
        bad = copy.deepcopy(self.cfg)
        bad['warm_start']['donor_config']['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'changed pinned'):
            self.warm.bind(bad, self.receipt)

    def test_equal_counts_do_not_hide_order_or_payload_changes(self):
        for kind in ('stream_order', 'database', 'indices'):
            receipt = copy.deepcopy(self.receipt)
            if kind == 'stream_order':
                receipt['streams'] = dict(reversed(list(receipt['streams'].items())))
            elif kind == 'database':
                receipt['streams']['pose']['database']['sha256'] = '0' * 64
            else:
                receipt['streams']['pose']['indices'] = self.variant('indices', [1, 0])
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'preparation settings'):
                self.warm.bind(self.cfg, receipt)

    def test_pin_relocation_preserves_row_content_identity(self):
        cfg = copy.deepcopy(self.cfg)
        receipt = copy.deepcopy(self.receipt)
        for name, stream in receipt['streams'].items():
            for key, suffix in (('database', '.sqlite'), ('receipt', '.json')):
                original = Path(stream[key]['path'])
                relocated = self.root / (name + '_relocated' + suffix)
                with relocated.open('xb') as target:
                    target.write(original.read_bytes())
                stream[key] = file_pin(relocated)
            cfg['streams'][name] = stream['receipt']
        self.assertEqual(self.warm.row_identity(receipt), self.warm.row_identity(self.receipt))
        self.warm.bind(cfg, receipt)

    def test_donor_optimizer_groups_recover_inherited_metadata(self):
        parent = dict(schema='carrier-c1-artifact-v1', head_init=dict(prefix='global_camera_head.',
                      copied=['trunk.0.weight', 'other.weight'], derived=['embed_pose.bias']))
        donor = copy.deepcopy(self.donor)
        donor['init_artifact']['artifact'] = self.variant('parent_inherited', parent)
        before = run.load(donor['preparation']['path'])
        before['config_sha256'] = run.identity(donor)
        seal = {**before['source_seal'], 'config_sha256': before['config_sha256']}
        seal.pop('sha256')
        seal['sha256'] = digest(seal)
        before['source_seal'] = seal
        donor['preparation'] = self.variant('prep_inherited', before)
        cfg = self.artifact(config_sha256=run.identity(donor), source_seal=seal, training_source_seal=seal)
        cfg['warm_start']['donor_config'] = self.variant('donor_inherited', donor)
        lineage = self.warm.bind(cfg, {**self.receipt, 'init_artifact': cfg['init_artifact']})
        loaded = load_fixture(self.root, {**self.receipt, 'init_artifact': cfg['init_artifact'],
                                         'warm_start': lineage}, Tiny())
        self.assertEqual(loaded.inherited_head_params, ['embed_pose.bias', 'trunk.0.weight'])

    def test_every_head_is_required(self):
        bad = copy.deepcopy(self.cfg)
        bad['init_artifact']['heads'].remove('frame_embeddings')
        with self.assertRaisesRegex(ValueError, 'all heads'):
            self.warm.validate(bad)
        model = Tiny()
        model.init_report = dict(step=200, kept=['frame_embeddings'], planned_init=[], head_tensors=4)
        with self.assertRaisesRegex(ValueError, 'export key'):
            self.warm.model_loaded(model, self.receipt['warm_start'])

    def test_warm_start_step_and_subsequent_exact_resume(self):
        self.assertEqual(self.warm.start_step(self.receipt), 200)
        self.assertEqual(self.warm.start_step(self.receipt, 250), 250)
        self.assertEqual(self.warm.start_step({}), 0)
        self.assertEqual(self.warm.start_step({}, 12), 12)
        for value in (199, True, '250'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.warm.start_step(self.receipt, value)

    def test_actual_train_entry_passes_absolute_step_and_fresh_optimizer(self):
        lineage = self.warm.bind(self.cfg, self.receipt)
        receipt = {**self.receipt, 'warm_start': lineage}
        captured = []

        def invoke(function, *args, **kwargs):
            values = inspect.signature(function).bind(*args, **kwargs).arguments
            captured.append(values)

        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, WORLD_SIZE='4', RANK='0', LOCAL_RANK='0',
                                            C1_EXPECT_FLA='0'))
            for target, name, replacement in (
                (run.rehearsal, 'enabled', lambda: True),
                (run.rehearsal, 'attempt_id', lambda: 'warm_cpu'),
                (run, 'prepared', lambda *a, **k: (receipt, {})),
                (run, 'authenticate', lambda *a: 'fixture-source'),
                (run, 'warn', lambda *a: None),
                (run, 'network_preflight', lambda *a: {}),
                (run, 'processor_for_receipt', lambda *a: None),
                (run, 'load_model', lambda *a, **k: self.model),
                (run, 'wrap_model', lambda model, *a, **k: model),
                (run, 'Rows', lambda *a: SimpleNamespace(close=lambda: None)),
                (run, 'run_lock', lambda *a: nullcontext()),
                (run, 'bind_output', lambda *a, **k: None),
                (run, 'run_or_exit', invoke),
                (run, 'agree', lambda *a: None),
                (run.signal, 'signal', lambda *a: None),
            ):
                stack.enter_context(patch.object(target, name, replacement))
            for name in ('init_process_group', 'new_group', 'broadcast_object_list', 'barrier',
                         'destroy_process_group'):
                stack.enter_context(patch.object(run.dist, name, lambda *a, **k: None))
            run.train(self.cfg)
        self.assertEqual(captured[0]['start_step'], 200)
        self.assertEqual(len(captured[0]['optimizer'].state), 0)
        attempt = run.load(Path(self.cfg['output']) / 'attempt_warm_cpu.json')
        self.assertEqual(attempt['first_step'], 201)
        self.assertEqual(attempt['warm_start'], lineage)

    def test_native_loop_records_absolute_checkpoint_and_metric_steps(self):
        lineage = self.warm.bind(self.cfg, self.receipt)
        self.model.warm_start_lineage = lineage
        checkpoints, exports, plans = [], [], []
        cfg = copy.deepcopy(self.cfg)
        cfg['recipe']['export_at_stop'] = True
        stop = [False]
        counts = {name: value['count'] for name, value in self.receipt['streams'].items()}
        out = self.root / 'loop'
        out.mkdir()

        def update(model, optimizer, rows, plan, rank, device, step, distributed, gates):
            plans.append((step, plan))
            stop[0] = True
            return {'wall_seconds': .001, 'head_metrics': {}}, None

        with patch.object(run, 'optimize_step', side_effect=update), \
             patch.object(run, 'checkpoint', side_effect=lambda *a, **k: checkpoints.append(a[4])), \
             patch.object(run, 'export', side_effect=lambda *a, **k: exports.append(a[4])), \
             patch.object(run, 'existing_export', return_value=False), \
             patch.object(run.rehearsal, 'enabled', return_value=False):
            report = run.run_steps(self.model, self.model, None, None, counts, out, cfg, {},
                                   torch.device('cpu'), start_step=200, stop=stop, distributed=False)
        self.assertEqual((report['first_step'], report['last_step']), (201, 201))
        self.assertEqual(checkpoints, [201])
        self.assertEqual(exports, [201])
        self.assertEqual(plans[0][0], 201)
        self.assertEqual(report['warm_start'], lineage)
        metrics = list(out.glob('metrics_*.jsonl'))
        self.assertEqual(run.load(metrics[0])['step'], 201)

    def test_production_quotas_and_sampler_suffix_match_every_rank(self):
        cfg = run.load(ROOT.parent / 'fourstream_template_inputs/k/28429cf9.json')
        counts = {'pointing': 20239, 'pose': 194987, 'routing': 57136, 'vqa': 114904}
        options = dict(training_mode='final', mix=cfg['recipe']['mix'], world=4, seed=17)
        baseline = list(data.mixed_indices(counts, 1000, **options))
        for step in (1, 50, 200, 800, 999):
            plan = next(data.mixed_indices(counts, step + 1, start_step=step, **options))
            self.assertEqual(plan, baseline[step])
            quotas = {name: sum(len(indices) for stream, indices in plan if stream == name) for name in counts}
            self.assertEqual(quotas, {'pointing': 32, 'pose': 64, 'routing': 64, 'vqa': 128})
            for rank in range(4):
                self.assertEqual([(name, ids[rank]) for name, ids in plan],
                                 [(name, ids[rank]) for name, ids in baseline[step]])

    def test_cross_root_aliases_and_parent_traversal_are_refused(self):
        self.warm.bind(self.cfg, self.receipt)
        for changes in ({'output': self.donor['preparation_output']},
                        {'preparation_output': self.donor['output']},
                        {'output': str(Path(self.donor['output']).parent / 'x/../469ddece')}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'nonoverlapping'):
                self.warm.bind({**self.cfg, **changes}, self.receipt)
        bad = copy.deepcopy(self.cfg)
        bad['warm_start']['donor_config']['path'] = str(self.root / 'x/../donor_config.json')
        with self.assertRaisesRegex(ValueError, 'absolute path'):
            self.warm.validate(bad)

    def test_native_loader_refuses_changed_payload_pins_and_missing_heads(self):
        artifact = run.load(self.cfg['init_artifact']['artifact']['path'])
        for field in ('heads', 'full_weights'):
            pin = {**artifact[field], 'sha256': 'f' * 64}
            cfg = self.artifact(**{field: pin})
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'changed pinned'):
                load_fixture(self.root, {**self.receipt, 'init_artifact': cfg['init_artifact']}, Tiny())
        state = dict(self.model.auxiliary_heads.state_dict())
        state.pop('frame_embeddings.weight')
        path = self.root / 'incomplete_heads.pt'
        torch.save(state, path)
        cfg = self.artifact(heads=file_pin(path))
        with self.assertRaisesRegex(ValueError, 'init heads differ'):
            load_fixture(self.root, {**self.receipt, 'init_artifact': cfg['init_artifact']}, Tiny())


class Template(unittest.TestCase):
    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('warm_config_template', ROOT / 'config_template.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_single_export_choice_derives_new_roots_without_a_release(self):
        root, cfg, donor, receipt, model = fixture()
        choice = dict(schema=self.module.SCHEMA, run='469ddece',
                      artifact=cfg['init_artifact']['artifact'], donor_config=cfg['warm_start']['donor_config'])
        result = self.module.instantiate(donor, choice)
        self.assertEqual(result, self.module.instantiate(donor, choice))
        self.assertEqual(result['status'], 'BLOCKED_UNSEALED')
        self.assertFalse(result['production_authorized'])
        self.assertNotEqual(result['run_key'], '469ddece')
        self.assertNotEqual(result['persistent_run_root'], '/home/jjyeung/okit/r/5da50f2b')
        self.assertEqual(result['config']['recipe'], donor['recipe'])
        self.assertEqual(result['config']['streams'], donor['streams'])
        self.assertEqual(result['config']['code'], self.module.UNSEALED)
        self.assertNotIn('preparation', result['config'])
        run.validate(result['config'])
        from student_pilot.s1_warm_start import bind
        bind(result['config'], receipt)
        write(root / 'unsealed_configuration_example.json', result)

    def test_template_rejects_extra_steps_wrong_runs_and_unpinned_choices(self):
        root, cfg, donor, receipt, model = fixture()
        choice = dict(schema=self.module.SCHEMA, run='469ddece',
                      artifact=cfg['init_artifact']['artifact'], donor_config=cfg['warm_start']['donor_config'])
        for delta in ({'step': 200}, {'run': 'fedcba98'},
                      {'artifact': {'path': '/fixture/artifact.json', 'sha256': '0' * 64}}):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                self.module.instantiate(donor, {**choice, **delta})


if __name__ == '__main__':
    unittest.main()
