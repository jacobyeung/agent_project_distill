"""Retained CPU fixtures for host evidence; no production inputs or training."""
from contextlib import ExitStack
from copy import deepcopy
import base64
import importlib.util
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from launch_r1 import entry, production_proof as proof
from student_pilot import carrier_c1_run as carrier
from student_pilot.p3_provenance import digest, encoded, file_pin, load, pinned, write
from student_pilot.r1_persisted import scope


def config():
    from student_pilot.carrier_c1_sweep import recipe_for
    from student_pilot.checkpoint_space import plan
    cfg = dict(training_mode='final', world_size=4, reference_world_size=32,
               mix=['pose', 'vqa', 'vqa', 'routing', 'pose', 'vqa', 'vqa', 'pointing', 'routing'],
               steps=1000, milestones=[100, 200, 400, 600, 800, 1000],
               scheduled_sampling=dict(max_own_probability=0, pose_open_deg=20., pose_full_deg=10.,
                                       fov_open_deg=2., depth_open_absrel=.25, ema_steps=100,
                                       force_from_step=None, exposure_from_step=None,
                                       exposure_probability=0., seed=17),
               recipe={})
    cfg['checkpoint_disk_guard'] = plan(recipe_for(cfg), retained_archive_copies=1)
    return cfg


class HostReceipt(unittest.TestCase):
    def setUp(self):
        self.area = Path(tempfile.mkdtemp(prefix='host24j_'))
        self.job = self.area/'job'
        self.root = self.job/'q'
        self.paths = {}
        self.entries = {}
        self.calls = []

    def pin(self, name, value, *, stage=False):
        raw = (encoded(value)+'\n').encode() if not isinstance(value, bytes) else value
        source = self.area/'bootstrap'/name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        pin = file_pin(source)
        self.paths[pin['sha256']] = str(source)
        pin['path'] = str(self.root/'u'/name)
        if stage:
            self.entries['u/'+name] = dict(payload=base64.b64encode(raw).decode(), sha256=pin['sha256'])
        return pin

    def fixture(self, *, bad_scene=False):
        cfg = config()
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
        db.execute('INSERT INTO rows VALUES (?,?)', (0, encoded(dict(qid='fixture', dataset='d1', scene='bad' if bad_scene else 'clean'))))
        database = self.pin('rows.db', db.serialize(), stage=True)
        db.close()
        division = self.pin('division.json', dict(train_scenes=['d1/clean'], heldout_scenes=['d1/bad']), stage=True)
        cfg.update(scene_division=division, dev_scene_exclusions=None, benchmark_scene_exclusions=None,
                   remove_files=[], streams={s:self.pin(s+'.json', dict(database=database, count=1, division=division), stage=True)
                                            for s in ('pose', 'vqa', 'routing', 'pointing')},
                   s1_routing={'fixture':True}, r2_sampling={},
                   r1_training=dict(mix=self.pin('card.json', dict(counting_admission='procedure_only_v1'), stage=True),
                                    routing_inputs={'fixture':True}, registry={}),
                   init_artifact=dict(artifact=self.pin('artifact.json', dict(step=400), stage=True)),
                   code=self.pin('code.json', dict(schema='fixture'), stage=True))
        cfg['preparation'] = self.pin('prep.json', dict(streams={}), stage=True)
        request = dict(job_tmp=str(self.job), binaries=['bash'],
                       routing_base=cfg['streams']['routing'], routing_inputs={'fixture':True},
                       routing_selection=self.pin('selection.json', dict(regenerated_sha256=digest({'synthetic_routing':True}))),
                       staging=self.pin('stage.json', dict(entries=self.entries)),
                       config=self.pin('config.json', cfg), room_audit={}, frame_roots=[str(self.job)],
                       memory_gib=8, weights=False, milestone=400)
        request['staged_pins'] = [request['config'], *cfg['streams'].values()]
        return cfg, request

    def dependencies(self, *, bind_error=False, bad_mode=False, incomplete=False):
        """Stub capacity producers; use real host checks, staging and final binder."""
        stack = ExitStack()
        stack.enter_context(patch.object(entry, 'TMP_NAMESPACE', self.area))
        stack.enter_context(scope(self.paths))
        stack.enter_context(patch('os.uname', return_value=SimpleNamespace(nodename='fixture-host')))
        stack.enter_context(patch('student_pilot.s1_routing.build', return_value={'synthetic_routing':True}))
        stack.enter_context(patch('student_pilot.mdg_parent.model_pin', return_value={}))
        stack.enter_context(patch('student_pilot.r1_rooms.verify_audit', return_value=dict(certifies='synthetic control flow', store={})))
        stack.enter_context(patch('student_pilot.r1_persisted.verify', return_value=dict(receipt=dict(step=400), paths={})))
        stack.enter_context(patch('student_pilot.r1_training.training_components', return_value={}))
        stack.enter_context(patch('launch_r1.p_opener_witness.produce', return_value={}))
        stack.enter_context(patch('student_pilot.r1_handover.bind_target', side_effect=lambda cfg, _:cfg))
        stack.enter_context(patch('student_pilot.r1_handover.donor', return_value=({}, {}, {}, {})))
        stack.enter_context(patch('student_pilot.r1_handover.compare_configs'))
        stack.enter_context(patch('student_pilot.r1_persisted.admission', return_value=dict(
            absolute_resume_step=400, init_milestone=400, paths={})))
        def prepare(pin, directory, *args, **kwargs):
            self.calls.append('prepare')
            cfg = load(pinned(pin))
            cfg['fixture_prepared'] = True
            write(directory/'config.json', cfg)
            return dict(config=file_pin(directory/'config.json'))
        def populate(cfg, directory):
            self.calls.append('population')
            cfg['fixture_population'] = True
            write(directory/'config.json', cfg)
            return file_pin(directory/'config.json')
        def audit(cfg, directory):
            self.calls.append(('audit', carrier.identity(cfg)))
            directory.mkdir(parents=True)
            if bad_mode:
                directory.chmod(0o755)
            return dict(complete=not incomplete, fixture_config_identity=carrier.identity(cfg))
        original_bind = proof.bind_handover
        def bind(cfg, directory):
            self.calls.append('bind')
            if bind_error:
                raise ValueError('FIXTURE_HANDOVER_FAILED')
            return original_bind(cfg, directory)
        stack.enter_context(patch('student_pilot.s1_admission.admit', side_effect=prepare))
        stack.enter_context(patch('student_pilot.r1_population.bind_prepared', side_effect=populate))
        stack.enter_context(patch('student_pilot.r1_loader.production_audit', side_effect=audit))
        stack.enter_context(patch.object(proof, 'bind_handover', side_effect=bind))
        return stack

    def run_q(self, request, **kwargs):
        with self.dependencies(**kwargs):
            return proof.run(request, self.root)

    def test_final_config_receipt_and_audit(self):
        _, request = self.fixture()
        result = self.run_q(request)
        self.assertEqual(result['status'], 'ADMIT', result)
        final = load(pinned(result['config']))
        host = load(pinned(result['host_receipt']))
        self.assertEqual(Path(result['host_receipt']['path']), self.root/'host.json')
        self.assertEqual(host['config_identity'], carrier.identity(final))
        self.assertEqual(host['loader_audit'], result['audit'])
        self.assertEqual(host['loader_audit']['fixture_config_identity'], carrier.identity(final))
        self.assertTrue(all(host['assertions'].values()))
        self.assertEqual(self.calls, ['prepare', 'population', 'bind', ('audit', carrier.identity(final))])
        population = load(self.root/'b/config.json')
        self.assertNotEqual(carrier.identity(population), carrier.identity(final))

    def test_disk_plan_mutation(self):
        cfg, request = self.fixture()
        cfg['checkpoint_disk_guard']['planned_full_states'] += 1
        request['config'] = self.pin('changed.json', cfg)
        request['staged_pins'] = [request['config']]
        self.assertRefused(request, 'R1_DISK_PLAN_DIFFERS')

    def test_routing_selection_mutation(self):
        _, request = self.fixture()
        request['routing_selection'] = self.pin('bad_selection.json', dict(regenerated_sha256='0'*64))
        self.assertRefused(request, 'R1_ROUTING_SELECTION_DIFFERS')

    def test_empty_root_mutation(self):
        _, request = self.fixture()
        self.root.mkdir(parents=True)
        (self.root/'occupied').write_text('fixture')
        # Exercise the root check independently of the stricter namespace check.
        with patch.object(entry, 'fresh_tmp', return_value=self.job):
            self.assertRefused(request, 'R1_HOST_ROOT_NOT_EMPTY')

    def test_job_tmp_mutation(self):
        _, request = self.fixture()
        self.job.mkdir()
        self.assertRefused(request, 'R1_HOST_JOB_TMP_NOT_FRESH')

    def test_runtime_binaries_mutation(self):
        _, request = self.fixture()
        request['binaries'] = ['HOST24J_NONEXISTENT_BINARY']
        self.assertRefused(request, 'R1_BINARY_MISSING:HOST24J_NONEXISTENT_BINARY')

    def test_runtime_binaries_empty_mutation(self):
        _, request = self.fixture()
        request['binaries'] = []
        self.assertRefused(request, 'R1_HOST_ASSERTION_FALSE:runtime_binaries')

    def test_directory_modes_mutation(self):
        _, request = self.fixture()
        self.assertRefused(request, 'R1_HOST_ASSERTION_FALSE:directory_modes', bad_mode=True)

    def test_scene_division_mutation(self):
        _, request = self.fixture(bad_scene=True)
        self.assertRefused(request, 'SCENE_DIVISION_REFUSED')

    def test_no_receipt_before_handover(self):
        _, request = self.fixture()
        self.assertRefused(request, 'FIXTURE_HANDOVER_FAILED', bind_error=True)
        self.assertFalse(any(isinstance(x, tuple) and x[0] == 'audit' for x in self.calls))

    def test_incomplete_loader_audit_refused(self):
        _, request = self.fixture()
        self.assertRefused(request, 'R1_HOST_ASSERTIONS_INCOMPLETE', incomplete=True)

    def test_environment_restored(self):
        _, request = self.fixture()
        saved = dict(os.environ)
        cwd, tempdir = Path.cwd(), tempfile.tempdir
        self.run_q(request, bind_error=True)
        self.assertEqual(dict(os.environ), saved)
        self.assertEqual(Path.cwd(), cwd)
        self.assertEqual(tempfile.tempdir, tempdir)

    def test_kit_stager_runs_after_freshness(self):
        _, request = self.fixture()
        from launch_r2.staging import stage_inputs
        events = []
        def stage(entries, root):
            self.assertTrue(self.job.is_dir())
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            self.assertEqual(Path.cwd(), self.job)
            events.append('stage')
            stage_inputs(entries, root)
        with self.dependencies():
            result = proof.run(request, self.root, stage=stage)
        self.assertEqual(result['status'], 'ADMIT', result)
        self.assertEqual(events, ['stage'])

    def assertRefused(self, request, name, **kwargs):
        result = self.run_q(request, **kwargs)
        self.assertEqual(result['status'], 'REFUSE')
        self.assertIn(name, result['refusal'])
        self.assertNotIn('host_receipt', result)
        self.assertFalse((self.root/'host.json').exists())

    def test_mode_p_bytes_match_base(self):
        base = Path(__file__).resolve().parents[2]/'tree_r1_base/launch_r1/entry.py'
        if not base.is_file():
            self.skipTest('Comparison needs the untouched base tree beside this tree')
        spec = importlib.util.spec_from_file_location('host24j_original_entry', base)
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        for label, change, options in (
                ('pass', None, {}), ('missing_binary', 'binary', {}),
                ('disk_plan', 'disk', {}), ('selection', 'selection', {}), ('scene', 'scene', {}),
                ('directory_modes', None, {'bad_mode':True}),
                ('loader_incomplete', None, {'incomplete':True})):
            with self.subTest(label=label):
                self.setUp()
                cfg, request = self.fixture(bad_scene=change == 'scene')
                if change == 'binary':request['binaries'] = ['HOST24J_NONEXISTENT_BINARY']
                if change == 'disk':cfg['checkpoint_disk_guard'] = {}
                if change == 'selection':request['routing_selection'] = self.pin('wrong.json', dict(regenerated_sha256='0'*64))
                results = []
                for module, name in ((original, 'before'), (entry, 'after')):
                    with self.dependencies(**options), patch.object(module, 'TMP_NAMESPACE', self.area):
                        value = module.frame_host(cfg, self.root, request)
                    results.append((encoded(value), (self.root/'receipt.json').read_bytes()))
                    self.job.rename(self.area/name)
                self.assertEqual(results[0], results[1])


class NativeAdmission(unittest.TestCase):
    def test_native_export_bind_audit_and_admit(self):
        """Use a tiny native export and logical rows; leave every admission gate real."""
        import torch
        from tests.test_carrier_c1 import fixture
        from tests.test_carrier_c1_run import RunnerTests
        from student_pilot import r1_handover as handover, r1_training as training
        from student_pilot import r2_policy
        from student_pilot.r1_loader import production_audit
        from launch_r1.p_handover_receipt import produce
        root = Path(tempfile.mkdtemp(prefix='native24j_'))
        def put(name, value):
            write(root/name, value)
            return file_pin(root/name)
        model = fixture(4, training_mode='final')[0]
        cfg = config()
        cfg.pop('checkpoint_disk_guard')
        cfg.update(base_identity='fixture', trace_program_version='3.13', heading_plane_min=.3, frame_layout='duplicate',
                   frame_count=32, frame_markers=True, max_pixels=None, min_pixels=None,
                   depth_fov_source='private', routing_opener_init='keep', geometry_connector='none',
                   carrier_placement='append_after_temporal_group_video_tokens_v1',
                   camera_overrides=dict(weight_scale=.04, weight_focal=2.))
        cfg['recipe'] = carrier.recipe_for(cfg)
        cfg['streams'] = {s:put(s+'.json', dict(database=dict(path=str(root/(s+'.db')), sha256=digest(s)), count=n))
                          for s, n in training.STREAMS.items()}
        ident = handover.export_identity(cfg)
        model_pin = put('model/config.json', model.config.to_dict())
        manifest = put('model.json', dict(root=str(root/'model'), files={'config.json':model_pin['sha256']}))
        preparation = dict(schema='c1-preparation-v1', config_sha256=ident, training_mode='final',
            streams={s:dict(receipt=p, database=load(pinned(p))['database'], count=training.STREAMS[s],
                            source_count=training.STREAMS[s]) for s,p in cfg['streams'].items()},
            recipe=cfg['recipe'], model=manifest, camera=model.auxiliary_heads.pose.settings,
            depth=dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1,2,3]))
        cfg['preparation'] = put('preparation.json', preparation)
        source = put('source.json', cfg)
        bound = dict(config_sha256=ident, preparation=cfg['preparation'], world_size=4, trainer_commit='fixture')
        carrier.bind_output(root/'producer', bound)
        with RunnerTests().local_collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            checkpoint = carrier.checkpoint(root/'producer/checkpoint', model,
                torch.optim.AdamW(carrier.parameter_groups(model)), bound, 400)
            carrier.export(root/'producer/m400', model, model, cfg, 400)
        cfg['init_artifact'] = dict(artifact=file_pin(root/'producer/m400/artifact.json'))
        donor = dict(config=source, preparation=cfg['preparation'], binding=file_pin(root/'producer/binding.json'), checkpoint=checkpoint)
        receipt = produce(donor, cfg['init_artifact']['artifact'], root/'handover.json',
                          job_id='synthetic-cpu', trainer_commit='fixture')
        card = dict(schema='r1-card-v1', steps=1000, seed=17, quotas=training.STREAMS, weight_scale=.04,
            cells=[dict(type=k, stream=s, rows_per_step=n) for s,k,n in (
                ('pose','pose',64), ('vqa','object_size',128), ('routing','recovery',32),
                ('routing','units',32), ('pointing','pointing',32))])
        card_pin = put('card.json', card)
        counts = {c['type']:c['rows_per_step']*250 for c in card['cells']}
        population = put('population.json', dict(schema='r1-population-v1', complete=True, after_all_filters=True,
            card_sha256=card_pin['sha256'], counts=counts, evidence=[source]))
        indices = {k:list(range(n)) for k,n in counts.items()}
        indices['units'] = list(range(8000,16000))
        cfg['r2_sampling'] = dict(schema='r1-sampling-v1', card=card_pin, population=population,
            indices=put('indices.json', dict(population_sha256=population['sha256'], cells=indices)))
        registry = r2_policy.slots()
        for name, slot in registry.items():
            slot['record'] = put('registry/'+name+'.json', dict(schema=slot['expected_schema'],
                component=name, component_class=slot['component_class'], phase=slot['phase'], inputs=[source],
                verdict='EXEMPT_FROZEN' if slot['component_class']=='external_frozen' else 'PROVEN_CLEAN',
                frozen=True, overlaps=[], checked_banks=list(r2_policy.SCOPE), exclusions_complete=True))
        cfg['r1_training'] = dict(schema='r1-training-v1', s2=False, stop_after_step=None, weight_scale=.04,
            mix=card_pin, registry=put('registry.json', registry), p_run=donor, handover_receipt=receipt,
            donor_config_sha256=ident)
        cfg['code'] = put('code.json', dict(schema='fixture'))
        pre_bind_identity = carrier.identity(cfg)
        cfg = load(pinned(proof.bind_handover(cfg, root/'final')))
        class Rows:
            def __init__(self, receipt, unused):pass
            def count(self, stream):return training.STREAMS[stream]*250
            def close(self):pass
            def row(self, stream, index):
                unit = ('cm','ft','inches')[index%3]
                return dict(qid=stream+'_'+str(index), question_type='object_abs_distance',
                    student_input={'question':'How far in '+unit+'?'},
                    target='<think>The printed measurement determines the distance.</think>A'), {}
        with patch('os.uname', return_value=SimpleNamespace(nodename='fixture-host')), \
                patch.object(carrier, 'prepared', return_value=(load(pinned(cfg['preparation'])),None)), \
                patch.object(carrier, 'Rows', Rows):
            audit = production_audit(cfg, root/'audit')
        host = dict(status='FAIL', assertions={k:True for k in entry.ASSERTIONS}, missing=[])
        # The isolated assertion tests exercise each real predicate. This fixture
        # concentrates on the unchanged native admission and handover boundary.
        (root/'receipt_root').mkdir(mode=0o700)
        entry.finish_host(cfg, root/'receipt_root', host, audit, named_refusals=True)
        cfg['r1_training']['host_receipt'] = put('host.json', host)
        cfg['r1_training']['review'] = put('review.json', dict(verdict='PASS', config_identity=carrier.identity(cfg)))
        prepared = load(pinned(cfg['preparation']))
        prepared.update(r1_training=deepcopy(cfg['r1_training']), config_sha256=carrier.identity(cfg))
        cfg['preparation'] = put('admitted_preparation.json', prepared)
        self.assertEqual(prepared['r1_training'], cfg['r1_training'])
        self.assertEqual(entry.admit(cfg), 400)
        absent = deepcopy(cfg)
        absent['r1_training'].pop('host_receipt')
        with self.assertRaisesRegex(ValueError, 'R1_HOST_ADMISSION_MISSING'):
            entry.admit(absent)
        for name, ident in (('foreign', '0'*64), ('input', carrier.identity(load(pinned(source)))),
                            ('before_bind', pre_bind_identity)):
            bad = deepcopy(cfg)
            bad['r1_training']['host_receipt'] = put(name+'_host.json', dict(host, config_identity=ident))
            with self.assertRaisesRegex(ValueError, 'R1_HOST_ADMISSION_MISSING'):
                entry.admit(bad)
        bad = deepcopy(cfg)
        bad['r1_training']['review'] = put('foreign_review.json', dict(verdict='PASS', config_identity='0'*64))
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT_REVIEW_PENDING'):
            entry.admit(bad)


if __name__ == '__main__':
    unittest.main()
