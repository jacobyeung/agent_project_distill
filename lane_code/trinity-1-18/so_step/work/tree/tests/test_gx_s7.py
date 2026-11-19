"""CPU regressions for pinned controls and authenticated GX code transitions."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from student_pilot import carrier_c1_run as run, g3t_online as gx
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_gx_carrier import configuration, root, collectives
from tests.test_gx_s6 import paired_cfg, reference_receipts, metric_file


def replace_json(path, value):
    path.write_text(json.dumps(value))


class S7ReferenceTests(unittest.TestCase):
    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

    def fixture(self, *, full_config=False):
        reference = root()
        cfg = paired_cfg(root(), reference)
        cfg['row_start_step'] = 800
        ref, bound = reference_receipts(cfg, reference, full_config=full_config)
        records = metric_file(reference, 'ctrl', range(1, 4))
        completed_path = reference/'run_ctrl.json'
        write(completed_path, dict(schema='c1-run-v1', status='PASS', binding=bound,
              first_step=1, last_step=3, world_size=8, steps=[r['ranks'] for r in records]))
        return cfg, reference, ref, bound

    def refuse_before_cuda(self, cfg):
        with patch.object(run, 'validate'), patch.object(torch.cuda, 'is_available') as cuda:
            with self.assertRaises((ValueError, TypeError)):
                run.train(cfg)
            cuda.assert_not_called()

    def test_pinned_legacy_and_full_config_reference_world_four_and_eight(self):
        for full in (False, True):
            cfg, reference, ref, bound = self.fixture(full_config=full)
            for world in (4, 8):
                with self.subTest(full_config=full, world=world):
                    cfg['world_size'] = world
                    cfg['recipe'] = run.recipe_for(cfg)
                    gx.normalize(cfg['geometry_online'])
                    before = copy.deepcopy(cfg)
                    self.assertEqual(sorted(run.gx_reference(cfg, 3)), [1, 2, 3])
                    self.assertEqual(cfg, before)

    def test_pin_required_and_binding_bytes_config_and_commit_must_match(self):
        for failure in ('missing', 'wrong_sha', 'wrong_config', 'wrong_commit', 'changed_bytes'):
            cfg, reference, ref, bound = self.fixture()
            pin = cfg['geometry_online']['fail_fast']['reference_binding']
            if failure == 'missing':
                cfg['geometry_online']['fail_fast'].pop('reference_binding')
            elif failure == 'changed_bytes':
                with (reference/'binding.json').open('a') as handle:
                    handle.write(' ')
            else:
                key = {'wrong_sha': 'sha256', 'wrong_config': 'config_sha256',
                       'wrong_commit': 'trainer_commit'}[failure]
                pin[key] = 'f'*64
            with self.subTest(failure=failure):
                self.refuse_before_cuda(cfg)

    def test_receipts_require_the_pinned_binding_or_the_matching_authenticated_attempt(self):
        for kind in ('attempt', 'run'):
            for failure in ('foreign', 'missing', 'orphan'):
                cfg, reference, ref, bound = self.fixture()
                path = reference/f'{kind}_ctrl.json'
                receipt = load(path)
                if failure == 'foreign':
                    receipt['binding'] = {**bound, 'trainer_commit': 'FOREIGN'}
                elif failure == 'missing':
                    receipt.pop('binding')
                else:
                    path = reference/f'{kind}_orphan.json'
                    # Foreign orphan attempts refuse even without metrics.
                    receipt['binding'] = {**bound, 'trainer_commit': 'FOREIGN'}
                replace_json(path, receipt)
                with self.subTest(kind=kind, failure=failure):
                    if kind == 'run' and failure == 'missing':
                        self.assertEqual(sorted(run.gx_reference(cfg, 3)), [1, 2, 3])
                    else:
                        self.refuse_before_cuda(cfg)

    def test_malformed_receipt_configs_never_fall_back_even_with_valid_snapshot(self):
        for kind in ('attempt', 'run'):
            for bad in (None, [], 'malformed', {'row_start_step': 0}, {'readout': None}):
                for snapshot in (False, True):
                    cfg, reference, ref, bound = self.fixture()
                    if snapshot:
                        write(reference/f'binding_config_{run.digest(bound)}.json', dict(binding=bound, config=ref))
                    path = reference/f'{kind}_ctrl.json'
                    replace_json(path, {**load(path), 'config': bad})
                    with self.subTest(kind=kind, bad=bad, snapshot=snapshot):
                        self.refuse_before_cuda(cfg)

    def test_legacy_preparation_schedule_still_must_match(self):
        for field in ('row_start_step', 'seed', 'mix', 'global_batch'):
            cfg, reference, ref, bound = self.fixture()
            if field == 'row_start_step':
                cfg[field] = 0
            else:
                cfg['recipe'][field] = {'seed': 18, 'mix': ['vqa']*4, 'global_batch': 16}[field]
            with self.subTest(field=field):
                self.refuse_before_cuda(cfg)

    def test_pin_schema_and_absent_reference_behavior(self):
        cfg, reference, ref, bound = self.fixture()
        block = cfg['geometry_online']
        for pin in (None, {}, {'sha256': 'x', 'config_sha256': 'b'*64, 'trainer_commit': 'A'},
                    {'sha256': 'a'*64, 'config_sha256': 'b'*64, 'trainer_commit': ''}):
            bad = copy.deepcopy(block); bad['fail_fast']['reference_binding'] = pin
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                gx.normalize(bad)
        cfg['geometry_online']['fail_fast'].pop('reference_binding')
        with self.assertRaises(ValueError):
            gx.normalize(cfg['geometry_online'])
        cfg['geometry_online']['fail_fast'].pop('reference')
        before = copy.deepcopy(cfg)
        self.assertIsNone(run.gx_reference(cfg, 3))
        gx.normalize(cfg['geometry_online'])
        self.assertEqual(cfg, before)
        cfg.pop('geometry_online')
        self.assertIsNone(run.gx_reference(cfg, 3))


class S7CodeTransitionTests(unittest.TestCase):
    def fixture(self, evidence='snapshot', *, legacy_reference=False):
        directory = root()
        cfg = configuration()
        cfg.update(output=str(directory), code=dict(path='/seal/A', sha256='a'*64),
                   preparation={'fixture': True})
        cfg['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.01, max_loss_ratio=2.)
        if legacy_reference:
            cfg['geometry_online']['fail_fast']['reference'] = '/verified/control'
        old = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit='A', world_size=1)
        write(directory/'binding.json', old)
        if evidence == 'checkpoint':
            run.bind_output(directory, old, cfg=cfg)
        model = torch.nn.Linear(2, 1)
        model.trace_program_version = cfg['trace_program_version']
        optimizer = torch.optim.AdamW(model.parameters())
        with collectives(), patch.object(run.dist, 'all_gather_object', side_effect=lambda out, v: out.__setitem__(0, v)):
            pin = run.checkpoint(directory/'checkpoint_000002', model, optimizer, old, 2)
        if evidence == 'snapshot':
            write(directory/f'binding_config_{run.digest(old)}.json', dict(binding=old, config=cfg))
        elif evidence == 'checkpoint':
            # Retain the snapshot elsewhere so only the checkpoint authenticates A.
            (directory/f'binding_config_{run.digest(old)}.json').rename(directory/'retained_snapshot_A.json')
        elif evidence == 'receipt':
            write(directory/'run_A.json', dict(binding=old, config=cfg))
        new = copy.deepcopy(cfg); new['code'] = dict(path='/seal/B', sha256='b'*64)
        if legacy_reference:
            new['geometry_online']['fail_fast']['reference_binding'] = dict(
                sha256='c'*64, config_sha256='d'*64, trainer_commit='CTRL')
        bound = {**old, 'config_sha256': run.identity(new), 'trainer_commit': 'B'}
        return directory, cfg, old, new, bound, pin, model, optimizer

    def test_authenticated_code_only_transition_restore_chain_and_milestone_replay(self):
        for evidence in ('snapshot', 'checkpoint', 'receipt'):
            with self.subTest(evidence=evidence):
                directory, cfg, old, new, bound, pin, model, optimizer = self.fixture(evidence)
                original = (directory/'binding.json').read_bytes()
                self.assertEqual(run.latest_resume(directory, bound, cfg=new), pin)
                with collectives(), patch.object(run.dist, 'all_gather_object', side_effect=lambda out, v: out.__setitem__(0, v)):
                    self.assertEqual(run.restore(pin, model, optimizer, bound, cfg=new), 2)
                rebind = run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin)
                record = load(rebind['path'])
                self.assertEqual(record['schema'], 'gx-code-rebind-v1')
                self.assertEqual((record['previous_trainer_commit'], record['trainer_commit']), ('A', 'B'))
                self.assertEqual((record['previous_code'], record['code']), (cfg['code'], new['code']))
                self.assertEqual(record['previous_config'], cfg)
                self.assertEqual((directory/'binding.json').read_bytes(), original)
                self.assertEqual([b for b, _ in run.output_bindings(directory)], [old, bound])
                self.assertEqual(run.latest_resume(directory, bound, cfg=new), pin)
                self.assertIsNone(run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin))
                milestone = directory/'m2'
                write(milestone/'weights.json', {}); write(milestone/'heads.json', {})
                write(milestone/'artifact.json', dict(schema='carrier-c1-artifact-v1', step=2,
                      config_sha256=old['config_sha256'], full_weights=file_pin(milestone/'weights.json'),
                      heads=file_pin(milestone/'heads.json')))
                self.assertTrue(run.existing_export(milestone, new, 2))
                third = copy.deepcopy(new); third['code'] = dict(path='/seal/C', sha256='c'*64)
                third_bound = {**bound, 'trainer_commit': 'C', 'config_sha256': run.identity(third)}
                next_pin = run.bind_output(directory, third_bound, resume=True, cfg=third, resume_pin=pin)
                self.assertEqual(load(next_pin['path'])['schema'], 'gx-code-rebind-v1')
                fourth = copy.deepcopy(third); fourth['geometry_online']['fail_fast']['max_loss_ratio'] = 3.
                fourth_bound = {**third_bound, 'config_sha256': run.identity(fourth)}
                last_pin = run.bind_output(directory, fourth_bound, resume=True, cfg=fourth, resume_pin=pin)
                self.assertEqual(load(last_pin['path'])['schema'], 'gx-rule-rebind-v1')
                self.assertEqual([b for b, _ in run.output_bindings(directory)], [old, bound, third_bound, fourth_bound])
                self.assertTrue(run.existing_export(milestone, fourth, 2))

    def test_authenticated_legacy_reference_config_can_acquire_required_pin(self):
        directory, cfg, old, new, bound, pin, model, optimizer = self.fixture(legacy_reference=True)
        with self.assertRaises(ValueError):
            gx.normalize(cfg['geometry_online'])
        gx.normalize(new['geometry_online'])
        self.assertEqual(run.latest_resume(directory, bound, cfg=new), pin)
        rebind = run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin)
        self.assertEqual(load(rebind['path'])['schema'], 'gx-rule-rebind-v1')
        self.assertEqual(run.output_bindings(directory)[-1][0], bound)

    def test_code_only_transition_refuses_missing_or_unauthenticated_old_config(self):
        for evidence in ('none', 'wrong_config', 'foreign_binding'):
            directory, cfg, old, new, bound, pin, model, optimizer = self.fixture('none')
            if evidence != 'none':
                write(directory/f'binding_config_{run.digest(old)}.json', dict(
                    binding={**old, 'trainer_commit': 'FOREIGN'} if evidence == 'foreign_binding' else old,
                    config={**cfg, 'steps': 99} if evidence == 'wrong_config' else cfg))
            with self.subTest(evidence=evidence):
                with self.assertRaises(ValueError):
                    run.latest_resume(directory, bound, cfg=new)
                with self.assertRaises(ValueError):
                    run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin)
                with self.assertRaises(ValueError):
                    run.restore(pin, model, optimizer, bound, cfg=new)
                self.assertEqual(list(directory.glob('binding_rebind_*.json')), [])

    def test_code_only_transition_refuses_other_identity_changes(self):
        directory, cfg, old, new, bound, pin, model, optimizer = self.fixture()
        changes = []
        for key, value in (('row_start_step', 800), ('steps', 99), ('output', str(root())),
                           ('streams', {'pose': {'changed': True}}), ('skip_unsupervised_lm', True)):
            changed = {**new, key: value}
            changes.append((key, {**bound, 'config_sha256': run.identity(changed)}, changed))
        changed = copy.deepcopy(new); changed['geometry_online']['connector']['rms_scale'] = 2.
        changes.append(('connector', {**bound, 'config_sha256': run.identity(changed)}, changed))
        changes += [('preparation', {**bound, 'preparation': {'foreign': True}}, new),
                    ('world', {**bound, 'world_size': 2}, new),
                    ('same_commit', {**bound, 'trainer_commit': 'A'}, new),
                    ('same_code', {**bound, 'config_sha256': run.identity(cfg)}, cfg)]
        for name, changed_bound, changed in changes:
            with self.subTest(name=name), self.assertRaises(ValueError):
                run.bind_output(directory, changed_bound, resume=True, cfg=changed, resume_pin=pin)
        self.assertEqual(list(directory.glob('binding_rebind_*.json')), [])

    def test_code_transition_chain_refuses_forks_wrong_kind_commits_and_code_pins(self):
        for failure in ('fork', 'kind', 'old_commit', 'new_commit', 'old_code', 'new_code', 'old_config'):
            directory, cfg, old, new, bound, pin, model, optimizer = self.fixture()
            record_pin = run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin)
            path = Path(record_pin['path']); record = load(path)
            if failure == 'fork':
                write(directory/'binding_rebind_fork.json', record)
            else:
                key, value = {'kind': ('schema', 'gx-rule-rebind-v1'),
                              'old_commit': ('previous_trainer_commit', 'FOREIGN'),
                              'new_commit': ('trainer_commit', 'FOREIGN'),
                              'old_code': ('previous_code', {}), 'new_code': ('code', {}),
                              'old_config': ('previous_config', {**cfg, 'steps': 99})}[failure]
                record[key] = value; replace_json(path, record)
            with self.subTest(failure=failure):
                with self.assertRaises(ValueError):
                    run.output_bindings(directory)
                with self.assertRaises(ValueError):
                    run.latest_resume(directory, bound, cfg=new)


if __name__ == '__main__':
    unittest.main()
