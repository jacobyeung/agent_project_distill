"""Second-round reviewer tests for the guarded warm-start candidate (e0770534)."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

W = Path('/scratch/jjyeung/orch_cd/leg_s1_review/work_warm_start_2')
sys.path.insert(0, str(W))
import test_warm_start as base  # noqa: E402  sealed tree plus the private overlay in W/student_pilot
import torch  # noqa: E402

run, data = base.run, base.data
from student_pilot import s1_warm_start as warm, s1_row_order  # noqa: E402
from student_pilot.p3_provenance import digest, file_pin, load, write  # noqa: E402


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


SCANNER_DIR = W / 'scanner/donor_row_scanner_07ca49df'
scan = module('scan_donor_rows', SCANNER_DIR / 'scan_donor_rows.py')
accept = module('accept_scan', SCANNER_DIR / 'accept_scan.py')


def sealed_lr(step, recipe, lr):
    w = math.ceil(recipe['steps'] * recipe['warmup_ratio'])
    if step <= w:
        return lr * step / w
    return lr * .5 * (1 + math.cos(math.pi * (step - w) / (recipe['steps'] - w)))


def make_db(path, rows, page_size=4096, reverse=False, key_order=None):
    conn = sqlite3.connect(path)
    try:
        conn.execute('PRAGMA page_size=%d' % page_size)
        conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
        items = list(rows)
        if reverse:
            items = items[::-1]
        conn.executemany('INSERT INTO rows VALUES (?,?,?)', items)
        conn.commit()
    finally:
        conn.close()
    return file_pin(path)


def read_db(pin):
    conn = sqlite3.connect(Path(pin['path']).as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        return list(conn.execute('SELECT i,row,target FROM rows ORDER BY i'))
    finally:
        conn.close()


class Round1Regression(unittest.TestCase):
    """The first review's three tests, with the receipt kept consistent as prepared() makes it."""

    def setUp(self):
        self.root, self.cfg, self.donor, self.receipt, self.model = base.fixture()

    def bound(self, step, heads=None):
        art = run.load(self.cfg['init_artifact']['artifact']['path'])
        art['step'] = step
        if heads is not None:
            art['heads'] = heads
        path = self.root / f'artifact_s{step}_{len(list(self.root.iterdir()))}.json'
        write(path, art)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = file_pin(path)
        # prepared() replaces the receipt's init_artifact with the config's (carrier_c1_run.py:669).
        return cfg, {**self.receipt, 'init_artifact': cfg['init_artifact']}

    def test_lr_and_rows_at_boundary_for_two_exports(self):
        for s in (200, 650):
            with self.subTest(s=s):
                cfg, receipt = self.bound(s)
                lineage = warm.bind(cfg, receipt)
                self.assertEqual(lineage['row_identity_method'], 'native-file-pins-v1')
                start = warm.start_step({'warm_start': lineage})
                self.assertEqual(start, s)
                captured, stop = [], [False]

                def update(model, optimizer, rows, plan, rank, device, step, distributed, gates):
                    captured.append((step, plan))
                    stop[0] = True
                    return {'wall_seconds': .001, 'head_metrics': {}}, None

                counts = {n: v['count'] for n, v in receipt['streams'].items()}
                out = self.root / f'loop_{s}'
                out.mkdir()
                with patch.object(run, 'optimize_step', side_effect=update), \
                     patch.object(run, 'checkpoint'), patch.object(run, 'export'), \
                     patch.object(run, 'existing_export', return_value=False), \
                     patch.object(run.rehearsal, 'enabled', return_value=False):
                    run.run_steps(self.model, self.model, None, None, counts, out, cfg, {},
                                  torch.device('cpu'), start_step=start, stop=stop, distributed=False)
                step, plan = captured[0]
                self.assertEqual(step, s + 1)
                recipe = run.recipe_for(cfg)
                self.assertEqual(recipe, run.recipe_for(self.donor))
                for g in run.parameter_groups(self.model):
                    got = run.learning_rate(step, {**recipe, 'learning_rate': g['initial_lr']})
                    self.assertEqual(got, sealed_lr(s + 1, recipe, g['initial_lr']))
                    self.assertNotEqual(got, sealed_lr(1, recipe, g['initial_lr']))
                original = list(data.mixed_indices(counts, recipe['steps'], training_mode='final',
                                                   mix=recipe['mix'], world=recipe['world_size']))
                self.assertEqual(plan, original[s])
                self.assertNotEqual(plan, original[s - 1])
                rows = run.Rows(receipt, None)
                try:
                    got = [(st, r, rows.row(st, ix[r])[0]['qid']) for st, ix in plan for r in range(4)]
                    exp = [(st, r, rows.row(st, ix[r])[0]['qid']) for st, ix in original[s] for r in range(4)]
                finally:
                    rows.close()
                self.assertEqual(got, exp)

    def test_author_inherited_metadata_with_consistent_receipt(self):
        # Author's test_donor_optimizer_groups_recover_inherited_metadata, with the receipt's
        # init_artifact equal to the config's as prepared() makes it.
        parent = dict(schema='carrier-c1-artifact-v1', head_init=dict(prefix='global_camera_head.',
                      copied=['trunk.0.weight', 'other.weight'], derived=['embed_pose.bias']))
        donor = copy.deepcopy(self.donor)
        path = self.root / 'parent_inherited.json'
        write(path, parent)
        donor['init_artifact']['artifact'] = file_pin(path)
        before = run.load(donor['preparation']['path'])
        before['config_sha256'] = run.identity(donor)
        seal = {**before['source_seal'], 'config_sha256': before['config_sha256']}
        seal.pop('sha256')
        seal['sha256'] = digest(seal)
        before['source_seal'] = seal
        write(self.root / 'prep_inherited.json', before)
        donor['preparation'] = file_pin(self.root / 'prep_inherited.json')
        art = run.load(self.cfg['init_artifact']['artifact']['path'])
        art.update(config_sha256=run.identity(donor), source_seal=seal, training_source_seal=seal)
        write(self.root / 'art_inherited.json', art)
        write(self.root / 'donor_inherited.json', donor)
        cfg = copy.deepcopy(self.cfg)
        cfg['init_artifact']['artifact'] = file_pin(self.root / 'art_inherited.json')
        cfg['warm_start']['donor_config'] = file_pin(self.root / 'donor_inherited.json')
        receipt = {**self.receipt, 'source_seal': seal, 'config_sha256': before['config_sha256'],
                   'init_artifact': cfg['init_artifact']}
        lineage = warm.bind(cfg, receipt)
        loaded = base.load_fixture(self.root, {**receipt, 'warm_start': lineage}, base.Tiny())
        self.assertEqual(loaded.inherited_head_params, ['embed_pose.bias', 'trunk.0.weight'])
        self.assertEqual(loaded.init_report['unselected_export_keys'], [])

    def test_round1_f2_extra_head_key_now_refuses(self):
        state = dict(self.model.auxiliary_heads.state_dict())
        state['stray_head.weight'] = torch.zeros(3)
        path = self.root / 'heads_extra.pt'
        torch.save(state, path)
        cfg, receipt = self.bound(200, heads=file_pin(path))
        lineage = warm.bind(cfg, receipt)
        with self.assertRaisesRegex(ValueError, 'export key'):
            base.load_fixture(self.root, {**receipt, 'warm_start': lineage}, base.Tiny())

    def test_round1_f1_changed_settings_with_consistent_new_pins_refuse(self):
        # Same shape as round 1's demonstration, but with stream pins consistent between config and
        # receipt (prepared() refuses inconsistent ones first): the settings change must still refuse.
        cfg, receipt = copy.deepcopy(self.cfg), copy.deepcopy(self.receipt)
        for name in cfg['streams']:
            path = self.root / ('rebuilt_' + name + '.json')
            write(path, {'fixture': name})  # identical content, new path
            cfg['streams'][name] = file_pin(path)
            receipt['streams'][name]['receipt'] = cfg['streams'][name]
        warm.bind(cfg, receipt)  # pure relocation binds
        for key, value in (('camera', {'weight_focal': 99.0}), ('depth', {'num_points_per_frame': 1}),
                           ('division', {'path': '/elsewhere', 'sha256': 'c' * 64})):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(cfg, {**receipt, key: value})


class RowGate(unittest.TestCase):
    """Producer (bundle scanner) against consumer (s1_row_order.verify) on a four-stream fixture with a
    two-source pose mixture, a VQA index map and a camera block."""

    def save(self, name, value):
        path = self.root / name
        write(path, value)
        return file_pin(path)

    def raw(self, name, text):
        path = self.root / name
        path.write_text(text)
        return file_pin(path)

    def setUp(self):
        self.root, cfg, donor, receipt, self.model = base.fixture()
        before = {k: copy.deepcopy(v) for k, v in receipt.items() if k not in ('init_artifact', 'warm_start')}
        before['camera'] = {'weight_focal': 2.0, 'supervision': {'path': '/fixed/sup.npz', 'sha256': 'e' * 64}}
        self.rows = {}
        for name in ('pointing', 'routing', 'vqa'):
            n = 19 + ('pointing', 'pose', 'routing', 'vqa').index(name)
            self.rows[name] = [(j, json.dumps({'qid': f'{name}:{j}', 'frames': {'path': f'/f/{j}.npz', 'sha256': '%064x' % j},
                                               'meta': {'a': j, 'b': 'x'}}), json.dumps({'value': j}))
                               for j in range(n)]
            before['streams'][name]['database'] = make_db(self.root / f'donor_{name}.sqlite', self.rows[name])
        # VQA keeps an explicit admitted index map (a subset in a non-trivial order).
        vqa_indices = [0, 2, 3, 5, 7, 8, 11, 13, 17, 19, 21]
        before['streams']['vqa']['indices'] = self.raw('donor_vqa_indices.json', json.dumps(vqa_indices))
        before['streams']['vqa']['count'] = len(vqa_indices)
        # Pose is a two-source database mixture with an order map.
        a = [(j, json.dumps({'qid': f'poseA:{j}'}), json.dumps({'pose': [j, .5]})) for j in range(7)]
        b = [(j, json.dumps({'qid': f'poseB:{j}'}), json.dumps({'pose': [j, 1.5]})) for j in range(9)]
        self.pose_rows = (a, b)
        order = [[k % 2, (k // 2) % (7 if k % 2 == 0 else 9)] for k in range(20)]
        self.pose_order = order
        pose = dict(kind='mix', count=20, order=self.raw('donor_pose_order.json', json.dumps(order)),
                    sources=[dict(kind='rows', count=7, frame_prefix='/data2/k7pd/',
                                  database=make_db(self.root / 'pose_a.sqlite', a)),
                             dict(kind='rows', count=9, frame_prefix=None,
                                  database=make_db(self.root / 'pose_b.sqlite', b))],
                    receipt=before['streams']['pose']['receipt'])
        before['streams']['pose'] = pose
        self.source = {}
        donor = copy.deepcopy(donor)
        for name, value in before['streams'].items():
            self.source[name] = dict(schema='fixture-stream-v1', stream=name, count=value['count'],
                                     camera={'weight_focal': 1.}, depth={'num_points_per_frame': 64},
                                     model={'path': '/fixed/model.json', 'sha256': 'a' * 64},
                                     division={'path': '/fixed/division.json', 'sha256': 'b' * 64})
            if 'database' in value:
                self.source[name]['database'] = value['database']
            pin = self.save(name + '_donor_receipt.json', self.source[name])
            donor['streams'][name] = pin
            value['receipt'] = pin
        before['config_sha256'] = run.identity(donor)
        seal = before['source_seal']
        seal['config_sha256'] = before['config_sha256']
        seal['sha256'] = digest({k: v for k, v in seal.items() if k != 'sha256'})
        donor['preparation'] = self.save('inputs/prep/s1_receipt.json', before)
        self.donor_pin = self.save('inputs/prep/config.json', donor)
        artifact = load(cfg['init_artifact']['artifact']['path'])
        artifact.update(config_sha256=before['config_sha256'], source_seal=seal, training_source_seal=seal)
        self.cfg = copy.deepcopy(cfg)
        self.cfg['streams'] = copy.deepcopy(donor['streams'])
        self.cfg['warm_start']['donor_config'] = self.donor_pin
        self.cfg['init_artifact']['artifact'] = self.save('guard_artifact.json', artifact)
        self.donor, self.before = donor, before
        self.receipt = {**copy.deepcopy(before), 'init_artifact': self.cfg['init_artifact']}
        self.counts = {name: value['count'] for name, value in before['streams'].items()}
        self.attestation = self.produce()

    def produce(self):
        scanner = scan.Scanner(self.root / 'inputs', self.root, self.donor_pin)
        output = scanner.snapshot(self.counts)
        output['resources']['cpus'] = min(output['resources']['cpus'], 2)  # operational bound only
        envelope = accept.accept(json.loads(json.dumps(output)),
                                 scan.hashlib.sha256((SCANNER_DIR / 'scan_donor_rows.py').read_bytes()).hexdigest(),
                                 self.donor_pin, self.donor['preparation'], self.counts)
        self.scanner_output = output
        return self.save('row_attestation.json', envelope)

    def rebuilt(self, mutate=None, page_size=8192, pose_order=None, vqa_indices=None, tag=''):
        """A fresh admission: new DB files (other page size, reverse insert order), new index/order
        files (other whitespace), new stream receipts at new paths. mutate(name, rows) edits rows."""
        cfg, receipt = copy.deepcopy(self.cfg), copy.deepcopy(self.receipt)
        for name in ('pointing', 'routing', 'vqa'):
            rows = copy.deepcopy(self.rows[name])
            if mutate:
                rows = mutate(name, rows)
            pin = make_db(self.root / f'new{tag}_{name}.sqlite', rows, page_size=page_size, reverse=True)
            receipt['streams'][name]['database'] = pin
            if 'scene_source' in receipt['streams'][name]:
                receipt['streams'][name]['scene_source']['database'] = pin
        idx = json.loads(Path(self.before['streams']['vqa']['indices']['path']).read_text()) \
            if vqa_indices is None else vqa_indices
        receipt['streams']['vqa']['indices'] = self.raw(f'new{tag}_vqa_indices.json', json.dumps(idx, indent=1))
        order = self.pose_order if pose_order is None else pose_order
        receipt['streams']['pose']['order'] = self.raw(f'new{tag}_pose_order.json', json.dumps(order, indent=2))
        for name in receipt['streams']:
            source = dict(self.source[name])
            if 'database' in source:
                source['database'] = receipt['streams'][name]['database']
            pin = self.save(f'new{tag}_{name}_receipt.json', source)
            cfg['streams'][name] = pin
            receipt['streams'][name]['receipt'] = pin
        return cfg, receipt

    def with_attestation(self, cfg, pin=None):
        cfg = copy.deepcopy(cfg)
        cfg['warm_start']['donor_row_order'] = pin or self.attestation
        return cfg

    # -- producer/consumer agreement --------------------------------------------------------------
    def test_scanner_and_consumer_hash_donor_identically(self):
        self.assertEqual(self.scanner_output['rows'], s1_row_order.fingerprint(self.before))
        self.assertEqual(self.scanner_output['scanner']['stream_order'], ['pointing', 'pose', 'routing', 'vqa'])

    def test_equal_content_other_layout_passes_only_with_attestation(self):
        cfg, receipt = self.rebuilt()
        for name in ('pointing', 'routing', 'vqa'):
            self.assertNotEqual(receipt['streams'][name]['database']['sha256'],
                                self.before['streams'][name]['database']['sha256'])
        self.assertNotEqual(receipt['streams']['pose']['order']['sha256'], self.before['streams']['pose']['order']['sha256'])
        with self.assertRaisesRegex(ValueError, 'row content/order'):
            warm.bind(cfg, receipt)  # byte gate stays the default
        lineage = warm.bind(self.with_attestation(cfg), receipt)
        self.assertEqual(lineage['row_identity_method'], s1_row_order.SCHEMA)
        self.assertEqual(lineage['row_identity_sha256'], self.scanner_output['rows']['sha256'])

    def test_byte_gate_default_accepts_identical_bytes_without_attestation(self):
        cfg, receipt = copy.deepcopy(self.cfg), copy.deepcopy(self.receipt)
        for name in receipt['streams']:
            pin = self.save(f'moved_{name}_receipt.json', self.source[name])
            cfg['streams'][name] = pin
            receipt['streams'][name]['receipt'] = pin
        self.assertEqual(warm.bind(cfg, receipt)['row_identity_method'], 'native-file-pins-v1')

    def test_one_changed_character_in_one_target_refuses(self):
        def mutate(name, rows):
            if name == 'vqa':
                i, row, target = rows[5]
                self.assertEqual(target, '{"value": 5}')
                rows[5] = (i, row, '{"value": 6}')
            return rows
        cfg, receipt = self.rebuilt(mutate, tag='t')
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            warm.bind(self.with_attestation(cfg), receipt)

    def test_one_changed_character_in_one_row_refuses(self):
        def mutate(name, rows):
            if name == 'pointing':
                i, row, target = rows[3]
                rows[3] = (i, row.replace('"b": "x"', '"b": "y"'), target)
            return rows
        cfg, receipt = self.rebuilt(mutate, tag='r')
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            warm.bind(self.with_attestation(cfg), receipt)

    def test_swapped_rows_refuse(self):
        def mutate(name, rows):
            if name == 'routing':
                rows[0], rows[1] = (0, *rows[1][1:]), (1, *rows[0][1:])
            return rows
        cfg, receipt = self.rebuilt(mutate, tag='s')
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            warm.bind(self.with_attestation(cfg), receipt)

    def test_missing_row_refuses(self):
        def mutate(name, rows):
            return rows[:-1] if name == 'routing' else rows
        cfg, receipt = self.rebuilt(mutate, tag='m')
        with self.assertRaisesRegex(ValueError, 'missing row'):
            warm.bind(self.with_attestation(cfg), receipt)

    def test_changed_index_map_and_pose_order_refuse(self):
        idx = json.loads(Path(self.before['streams']['vqa']['indices']['path']).read_text())
        idx[0], idx[1] = idx[1], idx[0]
        cfg, receipt = self.rebuilt(vqa_indices=idx, tag='i')
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            warm.bind(self.with_attestation(cfg), receipt)
        order = copy.deepcopy(self.pose_order)
        order[0], order[1] = order[1], order[0]
        cfg, receipt = self.rebuilt(pose_order=order, tag='o')
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            warm.bind(self.with_attestation(cfg), receipt)

    def test_stream_order_refuses_in_binder_and_in_attestation(self):
        cfg, receipt = self.rebuilt(tag='q')
        reordered = {**receipt, 'streams': dict(reversed(list(receipt['streams'].items())))}
        with self.assertRaisesRegex(ValueError, 'stream order'):
            warm.bind(self.with_attestation(cfg), reordered)
        with self.assertRaisesRegex(ValueError, 'row content differs'):
            s1_row_order.verify(self.attestation, self.donor_pin, self.donor['preparation'], reordered)

    def test_attestation_from_another_donor_or_preparation_refuses(self):
        value = load(self.attestation['path'])
        other = self.save('other_config.json', {**load(self.donor_pin['path']), 'note': 'other run'})
        for key, pin in (('config', other), ('preparation', other)):
            forged = self.save(f'attestation_{key}.json', {**value, key: pin})
            cfg, receipt = self.rebuilt(tag='a' + key)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'not bound to this donor'):
                warm.bind(self.with_attestation(cfg, forged), receipt)
        tampered = copy.deepcopy(value)
        tampered['rows']['streams'][0]['sha256'] = '0' * 64
        cfg, receipt = self.rebuilt(tag='z')
        with self.assertRaisesRegex(ValueError, 'malformed'):
            warm.bind(self.with_attestation(cfg, self.save('attestation_tampered.json', tampered)), receipt)

    def test_changed_effective_setting_or_type_refuses_even_with_attestation(self):
        cfg, receipt = self.rebuilt(tag='c')
        for changed in ({**receipt, 'camera': {**receipt['camera'], 'weight_focal': 2}},      # float -> int
                        {**receipt, 'camera': {**receipt['camera'], 'weight_focal': 2.5}},
                        {**receipt, 'camera': {**receipt['camera'],
                                               'supervision': {'path': '/moved/sup.npz', 'sha256': 'f' * 64}}}):
            with self.assertRaisesRegex(ValueError, 'preparation settings'):
                warm.bind(self.with_attestation(cfg), changed)
        moved = {**receipt, 'camera': {**receipt['camera'], 'supervision': {'path': '/moved/sup.npz', 'sha256': 'e' * 64}}}
        warm.bind(self.with_attestation(cfg), moved)  # path-only alias of the same content binds

    # -- documented limits (these pass by design; they record behaviour, not defects in the kernel) --
    def test_limit_row_key_order_is_not_bound(self):
        def mutate(name, rows):
            if name == 'vqa':
                rows = [(i, json.dumps(dict(reversed(list(json.loads(row).items())))), t) for i, row, t in rows]
            return rows
        cfg, receipt = self.rebuilt(mutate, tag='k')
        warm.bind(self.with_attestation(cfg), receipt)  # binds: canonical() sorts keys

    def test_limit_attestation_does_not_carry_scanner_provenance(self):
        # An envelope computed from the NEW admission (not by the bundle scanner from the donor's
        # databases) and wrapped in the donor pins is accepted: verify() cannot tell who produced it.
        def mutate(name, rows):
            if name == 'vqa':
                i, row, target = rows[5]
                rows[5] = (i, row, '{"value": 6}')
            return rows
        cfg, receipt = self.rebuilt(mutate, tag='f')
        forged = self.save('attestation_from_new_run.json', dict(
            schema=s1_row_order.ATTESTATION, config=self.donor_pin, preparation=self.donor['preparation'],
            rows=s1_row_order.fingerprint(receipt)))
        self.assertEqual(warm.bind(self.with_attestation(cfg, forged), receipt)['row_identity_method'],
                         s1_row_order.SCHEMA)


if __name__ == '__main__':
    unittest.main()
