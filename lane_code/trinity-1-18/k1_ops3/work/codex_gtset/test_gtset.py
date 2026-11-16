"""CPU integration and refusal tests; all artifacts remain in this workspace."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import uuid
from types import SimpleNamespace as NS
from unittest.mock import patch

from build_evidence import ROOT, OLD, KIT, MANIFEST, mapped, sha

sys.path[:0] = [str(KIT / 'work'), str(KIT / 'native_kit')]
import bindings as B
import k1_pipeline as K
import k1_phases as F
import gt_set as G
import gate
import k1_report as R
import build_tables
import numpy as np

# The deliverable pins deployment paths. Verify the scratch equivalent explicitly;
# never rewrite the deployment pins or modify the live deployment to run tests.
for path, expected in B.load(KIT / 'out/DEPENDENCIES.json').items():
    assert sha(mapped(path)) == expected, path
K._sources_verified = True
K._native()


def original(name):
    spec = importlib.util.spec_from_file_location('old_' + name, OLD / 'work' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD_K = original('k1_pipeline')
OLD_R = original('k1_report')
sys.path.insert(0, str(KIT / 'work'))
OLD_K._sources_verified = True
OLD_K._native()
RUN = ROOT / ('tests_' + uuid.uuid4().hex[:8])
RUN.mkdir()
print('Artifacts:', RUN, flush=True)


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')
    return path


class GTSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('K1_EXISTING_FIXTURE'):
            base = Path(os.environ['K1_EXISTING_FIXTURE']).resolve()
            assert base.is_relative_to(ROOT)
            cls.manifest = base / 'manifest.json';cls.m = B.load(cls.manifest)
            cls.captures = cls.m['captures'];cls.inv = base / 'inventory.json';cls.cache = base / 'old_cache'
            cls.all_set = base / 'all.json';cls.sub_set = base / 'subset.json';cls.sens_set = base / 'sensitivity.json'
            cls.all_entries = B.load(cls.all_set)
            cls.outputs = {tag: base / ('tables_' + tag) for tag in ['old', 'plain', 'all', 'subset', 'sensitivity']}
            cls.rows = [dict(id=r['id'], canonical=c['canonical'], type=r['type'], gt_value=r['gt_value'],
                             pred=r['gt_value'], label='trust', printed_cues={'status': 0},
                             training_target_available=True) for c in cls.captures for r in c['rows']]
            cls.fit_base = dict(fixture_only=False, metrics={'accept': {
                'refit': {'auc': .8, 'top1_accept_accuracy': .8},
                'current': {'auc': .8, 'top1_accept_accuracy': .8}}})
            return
        import rehearse
        from boundaries import CPU
        c, _ = rehearse.fixture(RUN / 'input')
        actual = B.load(MANIFEST)
        planned = actual['captures']
        chosen = [next(x for x in planned if x['k1_split'] == 'train'),
                  next(x for x in planned if x['k1_split'] == 'heldout')]
        chosen.append(next(x for x in planned if x['canonical'] not in {v['canonical'] for v in chosen}))
        cls.captures = []
        for i, real in enumerate(chosen):
            entry = copy.deepcopy(c)
            entry.update(canonical=real['canonical'], room=real['room'], k1_split=real['k1_split'],
                         gt_name_ids={'chair': [1], 'table': [2], 'lamp': [3]},
                         gt_name_ids_authority='explicit test fixture', model_row={'student_input': {}})
            for row in entry['rows']:
                row['id'] = str(i) + ':' + row['id']
            cls.captures.append(entry)
        cls.inv = save(RUN / 'inventory.json', dict(pilot_complete=True, pilot=[
            dict(canonical=x['canonical'], room=x['room'], split=x['k1_split']) for x in cls.captures]))
        cls.m = dict(production_ready=True, frame_staging_authorized=True, captures=cls.captures,
                     inventory=B.pin(cls.inv), gpu={})
        cls.manifest = save(RUN / 'manifest.json', cls.m)
        cls.cache = RUN / 'old_cache'
        # One old-code cache generation; clone immutable fixture arrays and bind each
        # independent fixture capture using the unchanged old cache receipt schema.
        first = cls.cache / B.digest(cls.captures[0]['canonical'])[:16]
        OLD_K.cache_capture(cls.captures[0], CPU(), first)
        # Add a spatially distinct proposal to exercise nonempty pair tables.
        # This is fixture data, bound with the unchanged cache receipt schema.
        raw = B.load(first / 'candidates.json')
        for frame in raw['frames'].values():
            chair = frame['phrases']['chair']
            extra = copy.deepcopy(frame['phrases']['table']['instances'][0])
            extra.update(query=1, source_prompt='chair')
            chair['instances'].append(extra)
            chair['all_instance_scores'].append(extra['score'])
            chair['n_above_floor'] = 2
        save(first / 'candidates.json', raw)
        r = B.load(first / 'CACHE_COMPLETE.json')
        r['files']['candidates.json'] = B.pin(first / 'candidates.json')
        save(first / 'CACHE_COMPLETE.json', r)
        for entry in cls.captures[1:]:
            dest = cls.cache / B.digest(entry['canonical'])[:16]
            shutil.copytree(first, dest)
            receipt = B.load(dest / 'CACHE_COMPLETE.json')
            receipt['capture_sha256'] = B.digest(entry)
            receipt['files'] = {n: B.pin(dest / n) for n in receipt['files']}
            save(dest / 'CACHE_COMPLETE.json', receipt)
        cls.all_entries = {x['canonical']: dict(x['gt'], pinned=True) for x in cls.captures}
        cls.all_set = save(RUN / 'all.json', cls.all_entries)
        cls.sub_set = save(RUN / 'subset.json', {x['canonical']: cls.all_entries[x['canonical']] for x in cls.captures[:2]})
        sensitive = copy.deepcopy(cls.all_entries)
        sensitive[cls.captures[0]['canonical']]['pinned'] = False
        cls.sens_set = save(RUN / 'sensitivity.json', sensitive)
        cls.outputs = {}
        for tag, set_path, sensitive in [('old', None, False), ('plain', None, False),
                                          ('all', cls.all_set, False), ('subset', cls.sub_set, False),
                                          ('sensitivity', cls.sens_set, True)]:
            dest = RUN / ('tables_' + tag)
            if tag == 'old': OLD_K.tables(cls.m, cls.cache, dest)
            else: K.tables(cls.m, cls.cache, dest, set_path, sensitive)
            cls.outputs[tag] = dest
        cls.rows = [dict(id=r['id'], canonical=c['canonical'], type=r['type'], gt_value=r['gt_value'],
                         pred=r['gt_value'], label='trust', printed_cues={'status': 0},
                         training_target_available=True) for c in cls.captures for r in c['rows']]
        cls.fit_base = dict(fixture_only=False, metrics={'accept': {
            'refit': {'auc': .8, 'top1_accept_accuracy': .8},
            'current': {'auc': .8, 'top1_accept_accuracy': .8}}})

    def report_cli(self, tag, *, module=R, rows=None, flags=True, suffix=''):
        table_path = self.outputs[tag] / 'TABLE_RECEIPT.json'
        t = B.load(table_path)
        fit = copy.deepcopy(self.fit_base)
        fit['inputs'] = {pin['path']: pin['sha256'] for pin in t['files'].values()}
        fit['inputs'][str(self.inv)] = sha(self.inv)
        if 'gt_set' in t:
            fit.update(gt_set=t['gt_set'], table_receipt=G.pin(table_path))
        fit_path = save(RUN / ('fit_' + tag + suffix + '.json'), fit)
        selected = t.get('gt_set', {}).get('captures', [c['canonical'] for c in self.captures])
        rows = rows if rows is not None else [r for r in self.rows if r['canonical'] in selected]
        row_path = RUN / ('rows_' + tag + suffix + '.jsonl')
        row_path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        out = RUN / ('report_' + tag + suffix + '.json')
        argv = ['report', '--rows', str(row_path), '--inventory', str(self.inv), '--manifest',
                str(self.manifest), '--fit', str(fit_path), '--out', str(out)]
        if 'gt_set' in t and flags:
            argv += ['--gt-set', t['gt_set']['path'], '--ids-from', str(table_path)]
            if tag == 'sensitivity': argv += ['--sensitivity']
        with patch.object(sys, 'argv', argv): module.main()
        return out

    def test_a_tables_identical_with_all_set_and_default(self):
        for name in ['candidates.jsonl', 'pairs.jsonl']:
            expected = (self.outputs['old'] / name).read_bytes()
            self.assertTrue(expected)
            self.assertEqual(expected, (self.outputs['plain'] / name).read_bytes())
            self.assertEqual(expected, (self.outputs['all'] / name).read_bytes())
        # Receipts carry new provenance; path-dependent legacy pins are compared
        # after mapping only the different output directory names.
        old = (self.outputs['old'] / 'TABLE_RECEIPT.json').read_text()
        plain = (self.outputs['plain'] / 'TABLE_RECEIPT.json').read_text()
        self.assertEqual(old.replace(str(self.outputs['old']), 'OUT'), plain.replace(str(self.outputs['plain']), 'OUT'))

    def test_a_report_default_bytes_and_all_set_statistics_identical(self):
        old = self.report_cli('old', module=OLD_R).read_bytes()
        plain = self.report_cli('plain').read_bytes()
        self.assertEqual(old, plain)
        selected = B.load(self.report_cli('all'))
        for key in ['analysis', 'gt_set', 'expected_rows', 'table_receipt']: selected.pop(key)
        self.assertEqual(old, (json.dumps(selected, indent=2) + '\n').encode())

    def test_b_subset_receipt_and_tables(self):
        t = B.load(self.outputs['subset'] / 'TABLE_RECEIPT.json')
        self.assertEqual(t['gt_set']['sha256'], sha(self.sub_set))
        self.assertEqual(t['gt_set']['n'], 2)
        self.assertEqual(t['gt_set']['skipped'], [self.captures[2]['canonical']])
        for name in ['candidates.jsonl', 'pairs.jsonl']:
            rows = [json.loads(l) for l in (self.outputs['subset'] / name).read_text().splitlines()]
            self.assertTrue(rows)
            self.assertLessEqual({r['scene'] for r in rows}, set(t['gt_set']['captures']))
        self.assertEqual(B.load(self.report_cli('subset'))['expected_rows'], 6)

    def test_c_unpinned_requires_flag_and_first_lines(self):
        with self.assertRaisesRegex(ValueError, '--sensitivity'):
            K.tables(self.m, self.cache, RUN / 'refused_unpinned', self.sens_set)
        for path in [self.outputs['sensitivity'] / 'TABLE_RECEIPT.json', self.report_cli('sensitivity')]:
            self.assertIn('SENSITIVITY', path.read_text().splitlines()[0])
            self.assertEqual(B.load(path)['gt_set']['unpinned'], 1)

    def test_d_missing_cache_fails(self):
        with self.assertRaises(FileNotFoundError):
            K.tables(self.m, RUN / 'missing_cache', RUN / 'refused_missing', self.all_set)

    def test_d_capture_digest_mismatch_fails(self):
        m = copy.deepcopy(self.m)
        m['captures'][0]['rows'][0]['gt_value'] += 1
        with self.assertRaisesRegex(ValueError, 'Cache capture differs'):
            K.tables(m, self.cache, RUN / 'refused_digest', self.all_set)

    def test_d_corrupt_cache_pin_fails(self):
        dest = RUN / 'corrupt_cache' / B.digest(self.captures[0]['canonical'])[:16]
        shutil.copytree(self.cache / dest.name, dest)
        r = B.load(dest / 'CACHE_COMPLETE.json')
        r['files']['candidates.json'] = dict(path=str(dest / 'candidates.json'), sha256='0' * 64)
        save(dest / 'CACHE_COMPLETE.json', r)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            K.tables(self.m, dest.parent, RUN / 'refused_corrupt', self.all_set)

    def test_e_old_cache_accepted_and_manifest_unchanged(self):
        before = B.digest(self.m)
        for c in self.captures:
            raw, geo, receipt = K.cached(c, self.cache / B.digest(c['canonical'])[:16])
            self.assertEqual(receipt['capture_sha256'], B.digest(c))
        self.assertEqual(before, B.digest(self.m))

    def test_manifest_checks_skip_absent_unselected_gt(self):
        m = copy.deepcopy(self.m)
        m['captures'][2]['gt']['path'] = str(RUN / 'absent_unselected.npz')
        with self.assertRaises(FileNotFoundError): OLD_K.check_manifest(m, 'downstream')
        self.assertIs(K.check_manifest(m, 'downstream', self.sub_set), m)
        bad = copy.deepcopy(m);bad['captures'] = bad['captures'][:2]
        with self.assertRaisesRegex(ValueError, 'exact selected capture set'):
            K.check_manifest(bad, 'downstream', self.sub_set)

    def test_set_hash_and_pinned_manifest_guards(self):
        x = copy.deepcopy(self.all_entries)
        x[self.captures[0]['canonical']]['sha256'] = '0' * 64
        p = save(RUN / 'wrong_pin.json', x)
        with self.assertRaisesRegex(ValueError, 'manifest pin'):
            K.tables(self.m, self.cache, RUN / 'refused_manifest_pin', p)
        x[self.captures[0]['canonical']]['pinned'] = False
        p = save(RUN / 'wrong_unpinned_hash.json', x)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            K.tables(self.m, self.cache, RUN / 'refused_set_hash', p, True)

    def test_invalid_set_and_phase_options(self):
        for name, data in [('empty', {}), ('unknown', {'bad/capture': next(iter(self.all_entries.values()))})]:
            p = save(RUN / (name + '.json'), data)
            with self.assertRaises(ValueError): K.tables(self.m, self.cache, RUN / ('refused_' + name), p)
        with self.assertRaises(ValueError): G.load(None, True)
        with self.assertRaisesRegex(ValueError, 'downstream only'): K.check_manifest(self.m, 'own', self.all_set)
        p = RUN / 'duplicates.json';p.write_text('{"x":{},"x":{}}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'): G.load(p)

    def test_report_missing_extra_and_wrong_capture_rows_refused(self):
        rows = [r for r in self.rows if r['canonical'] in {c['canonical'] for c in self.captures[:2]}]
        for suffix, values in [('missing', rows[:-1]), ('extra', self.rows)]:
            with self.assertRaisesRegex(ValueError, 'denominator'):
                self.report_cli('subset', rows=values, suffix=suffix)
        wrong = copy.deepcopy(rows);wrong[0]['canonical'] = self.captures[1]['canonical']
        with self.assertRaisesRegex(ValueError, 'row capture'):
            self.report_cli('subset', rows=wrong, suffix='wrong_capture')
        with self.assertRaisesRegex(ValueError, 'receipt differs'):
            self.report_cli('subset', flags=False, suffix='no_options')

    def test_old_code_does_not_support_declared_sets(self):
        with self.assertRaises(TypeError): OLD_K.tables(self.m, self.cache, RUN / 'old_option', gt_set=self.sub_set)
        with self.assertRaisesRegex(ValueError, 'denominator'):
            self.report_cli('subset', module=OLD_R, flags=False, suffix='old_denominator')

    def refit_adapter(self):
        # Both authorized environments lack sklearn. Execute the real train,
        # split, feature-audit and probability functions with estimator stand-ins.
        # This tests the added provenance guards, not estimator numerics.
        source = ast.parse((KIT / 'work/refit/train.py').read_text())
        functions = [n for n in source.body if isinstance(n, ast.FunctionDef)
                     and n.name in {'train', 'split_rows', 'audit_features', 'probability'}]
        read = lambda p: [json.loads(l) for l in Path(p).read_text().splitlines()]
        candidate = read(self.outputs['all'] / 'candidates.jsonl')[0]
        pair = read(self.outputs['all'] / 'pairs.jsonl')[0]
        models = {}
        for key, features in [('accept', list(candidate['features'])), ('pairs', list(pair['f']))]:
            models[key] = dict(features=features, mean=[0.] * len(features), scale=[1.] * len(features),
                               coef=[0.] * len(features), intercept=0.)
        fixture_root = RUN / 'refit_dependencies'
        model_path = fixture_root / 'devs1_masks/out/kit/work/vendor/MODELS.json'
        model_path.parent.mkdir(parents=True, exist_ok=True)
        save(model_path, models)
        source_path = fixture_root / 'grd_selector/work/setsel'
        source_path.mkdir(parents=True, exist_ok=True)
        for name in ['build.py', 'fit.py', 'fit_pairs.py', 'setlib.py']:
            (source_path / name).write_text('# Explicit test dependency stand-in; not deployable.\n')
        class Estimator:
            def fit(self, x, y): return NS(fixture_estimator=True)
        namespace = dict(Path=Path, json=json, np=np, gate=gate, G=G,
                         pickle=__import__('pickle'), SOURCE=source_path,
                         versions=lambda: dict(test='ESTIMATOR_STAND_INS_NO_SKLEARN'),
                         metrics=lambda *args: dict(auc=.8, top1_accept_accuracy=.8),
                         exported=lambda model, feats: models['accept' if feats == models['accept']['features'] else 'pairs'],
                         L=NS(load=lambda p: (None, {'fixture': read(p)}),
                              FEATS={'portable_np': models['accept']['features']}, PFEATS=models['pairs']['features']),
                         fit_pairs=NS(load=lambda p: (read(p), None, None)),
                         fit=NS(fit_predict=lambda *args: (None, NS(fixture_estimator=True), None),
                                model=lambda *args: Estimator()))
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(KIT / 'work/refit/train.py'), 'exec'), namespace)
        def invoke(*args, **kwargs):
            with patch.object(gate, 'ROOT', fixture_root):
                return namespace['train'](*args, **kwargs)
        return invoke

    def test_refit_and_render_propagate_subset_and_sensitivity(self):
        train = self.refit_adapter()
        for tag, gt_set, sensitivity in [('subset', self.sub_set, False), ('sensitivity', self.sens_set, True)]:
            tables = self.outputs[tag]
            fit = RUN / ('trained_' + tag)
            train(tables / 'candidates.jsonl', tables / 'pairs.jsonl', self.inv, fit,
                  gt_set=gt_set, sensitivity=sensitivity)
            receipt = B.load(fit / 'FIT_RECEIPT.json')
            meta = B.load(tables / 'TABLE_RECEIPT.json')['gt_set']
            self.assertEqual(receipt['gt_set'], meta)
            self.assertEqual(receipt['table_receipt'], G.pin(tables / 'TABLE_RECEIPT.json'))
            out = RUN / ('render_' + tag)
            K.responses(self.m, self.cache, fit, out, gt_set, sensitivity)
            self.assertEqual(B.load(out / 'RENDER_RECEIPT.json')['gt_set'], meta)
            actual = [json.loads(l) for l in (out / 'K1_ANALYSIS_INPUT.jsonl').read_text().splitlines()]
            self.assertEqual({r['canonical'] for r in actual}, set(meta['captures']))
            for c in self.captures:
                dest = out / B.digest(c['canonical'])[:16]
                self.assertEqual(dest.exists(), c['canonical'] in meta['captures'])
                if dest.exists(): self.assertEqual(B.load(dest / 'COMPLETE.json')['gt_set'], meta)
            if sensitivity:
                for p in [fit / 'FIT_RECEIPT.json', out / 'RENDER_RECEIPT.json']:
                    self.assertIn('SENSITIVITY', p.read_text().splitlines()[0])
            argv = ['report', '--rows', str(out / 'K1_ANALYSIS_INPUT.jsonl'), '--inventory', str(self.inv),
                    '--manifest', str(self.manifest), '--fit', str(fit / 'FIT_RECEIPT.json'),
                    '--ids-from', str(tables / 'TABLE_RECEIPT.json'), '--out', str(out / 'REPORT.json')]
            if sensitivity: argv += ['--sensitivity']
            with patch.object(sys, 'argv', argv): R.main()
            self.assertEqual(B.load(out / 'REPORT.json')['gt_set'], meta)

    def test_refit_rejects_cross_set_and_unflagged_sensitivity(self):
        train = self.refit_adapter()
        for tag, gt_set in [('subset', self.all_set), ('sensitivity', self.sens_set)]:
            tables = self.outputs[tag]
            with self.assertRaises(ValueError):
                train(tables / 'candidates.jsonl', tables / 'pairs.jsonl', self.inv,
                      RUN / ('bad_refit_' + tag), gt_set=gt_set)

    def test_real_phase_copies_preserve_bindings(self):
        real = B.load(MANIFEST)
        binding = B.load(ROOT / 'real_phase_copies/BINDING.json')
        deployed = B.load(ROOT / 'evidence/identity_proof.json')['deployment_source_identity']
        self.assertEqual(binding['sources'], deployed)
        self.assertEqual(binding['producer_sha256'], sha(KIT / 'work/k1_phases.py'))
        self.assertEqual(binding['manifest_sha256'], B.digest(real))
        results = []
        for name in ['01949c4249271126', '0269f4aee84d8be3']:
            c = next(c for c in real['captures'] if B.digest(c['canonical'])[:16] == name)
            with patch.object(B, 'source_identity', return_value=deployed):
                dest, receipt = F.checked_phase(c, ROOT / 'real_phase_copies', 'tower_sam')
            self.assertEqual(receipt['capture_sha256'], B.digest(c))
            # A tower/SAM phase is not a converted cache. Keep this fail-closed.
            with self.assertRaises(FileNotFoundError): K.cached(c, dest)
            results.append(dict(canonical=c['canonical'], phase_check='PASS',
                                cached='requires CACHE_COMPLETE.json and geometry.npz after own/convert',
                                receipt_sha256=sha(dest / 'PHASE_COMPLETE.json')))
        save(ROOT / 'evidence/real_phase_checks.json', results)

    def test_real_proposals_enter_tables_with_fixture_own_geometry(self):
        """Bridge test only: real tower/SAM, explicitly synthetic own depth/gravity."""
        from student_pilot.tower_read import TowerState
        real = B.load(MANIFEST)
        cache = RUN / 'real_proposals_fixture_geometry'
        captures = []
        proof = []
        for name in ['01949c4249271126', '0269f4aee84d8be3']:
            c = next(c for c in real['captures'] if B.digest(c['canonical'])[:16] == name)
            captures.append(c)
            phase = ROOT / 'real_phase_copies' / name
            receipt = B.load(phase / 'PHASE_COMPLETE.json')
            dest = cache / name
            dest.mkdir(parents=True)
            state = TowerState.from_npz(phase / 'tower.npz')
            # No production own result exists. Equal-depth scaling and fixed
            # gravity serve only as a schema/loader fixture, never a score.
            geometry = B.geometry.convert(state, state.depth_grid.copy(), np.array([0., -1., 0.]),
                                          receipt['source_hw'], dest / 'geometry.npz')
            for file in ['candidates.json', 'parity_raw.jsonl']:
                (dest / file).symlink_to(phase / file)
            B.write(dest / 'CACHE_COMPLETE.json', dict(
                capture_sha256=B.digest(c), checkpoint=receipt['checkpoint'], synthetic=True,
                geometry=geometry, sources=receipt['sources'],
                files={n: B.pin(dest / n) for n in ['geometry.npz', 'candidates.json', 'parity_raw.jsonl']},
                phase='unselected_cache_no_responses', fixture_note='TEST ONLY: fabricated own depth/gravity'))
            for module in [OLD_K, K]:
                raw, geo, loaded = module.cached(c, dest)
                self.assertTrue(loaded['synthetic'])
                self.assertEqual(loaded['capture_sha256'], B.digest(c))
            proof.append(dict(canonical=c['canonical'], old_cached='PASS', patched_cached='PASS',
                              own_geometry='TEST FIXTURE ONLY', real_proposals_sha256=sha(phase / 'candidates.json')))
        subset = save(RUN / 'two_real_test_set.json', {c['canonical']: dict(c['gt'], pinned=True) for c in captures})
        visited = []
        def entry(c, raw, geo, gt):
            visited.append(c['canonical'])
            self.assertTrue(raw['frames'])
            return [], []
        # Exercise tables' actual cached() entry checks, without reading GT or
        # computing real-capture labels/statistics in this compatibility proof.
        with patch.object(K, 'gt_arrays', return_value={'test_only': True}), patch.object(build_tables, 'build_capture', side_effect=entry):
            K.tables(real, cache, RUN / 'real_cache_entry_checks', subset)
        self.assertEqual(set(visited), {c['canonical'] for c in captures})
        save(ROOT / 'evidence/real_cache_bridge.json', proof)


if __name__ == '__main__':
    unittest.main(verbosity=2)
