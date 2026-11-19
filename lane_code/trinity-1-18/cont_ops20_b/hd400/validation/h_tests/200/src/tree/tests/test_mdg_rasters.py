"""Retained synthetic MDG exports and GT union-raster regression fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from student_pilot import mdg_eval as E, mdg_rasters as R
from student_pilot.p3_provenance import digest, file_pin, load, write


class MDGRasters(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='mdg-rasters-', dir=os.environ['LANE_TEST_OUTPUT']))
        self.export, self.gt, self.artifact = [self.root/p for p in ('export', 'gt', 'artifact')]
        for path in (self.export, self.gt, self.artifact):
            path.mkdir()
        self.scene = 'scene0001_00'
        self.meta = self.artifact/'mdg.json'
        write(self.meta, dict(tau=.6, schema='synthetic-cpu-fixture'))
        self.names = ['chair', 'couch', 'no such object']
        self.entry = dict(scene='scannet/'+self.scene, frame_indices=list(range(32)))
        self.audit = dict(entry=self.entry, tau=.6, mdg_artifact=dict(meta=file_pin(self.meta)))
        shape = (3, 32)
        self.values = dict(prob=np.zeros(shape), frame_prob=np.zeros(shape), clip_prob=np.ones(3),
            iou=np.ones(shape), uv=np.zeros((*shape, 2)), area=np.ones(shape),
            mask=np.ones((*shape, 2, 5), dtype=bool))
        self.values['prob'][0, :7] = [.6, 1., .2, .9, .6, .7, .9]
        self.values['frame_prob'][:] = self.values['prob']
        self.inst = np.zeros((32, 20, 50), np.int32)
        for k, n in enumerate((2, 1, 10, 50, 51, 0, 100)):
            self.inst[k].flat[:n] = 7
        self.inst[0].flat[1] = 9
        self.valid = np.ones(32, dtype=bool)
        self.valid[6] = False
        self.ids, self.labels = np.array([7, 9, 12]), np.array(['chair', 'chair', 'sofa'])
        self.npz = self.export/'anchors.npz'
        self.save_export()
        self.save_gt()
        self.paths = {k: self.root/(k+'.json') for k in ('frozen', 'dev', 'vsi', 'vsti')}
        write(self.paths['frozen'], dict(tune_scenes=[]))
        self.paths['dev'].write_text('')
        write(self.paths['vsi'], [dict(dataset='scannet', scene_name=self.scene)])
        write(self.paths['vsti'], [])

    def save_export(self):
        # Each rewrite uses a new immutable export pathname.
        if self.npz.exists():
            self.npz = self.export/(self.npz.stem+'-next.npz')
        E.save_npz(self.npz, self.names, self.values, self.audit)

    def save_gt(self, scene=None, indices=None):
        path = self.gt/((scene or self.scene)+'.npz')
        with path.open('wb') as stream:
            np.savez_compressed(stream, inst=self.inst, ids=self.ids, labels=self.labels,
                valid=self.valid, frame_indices=list(range(32)) if indices is None else indices)

    def run_read(self, name='RASTERS.json'):
        return R.run(self.export, self.artifact, self.root/name, gt_root=self.gt, **self.paths)

    def test_packed_export_union_counts_bins_and_metrics(self):
        result = self.run_read()
        overall = result['overall']
        counts = overall['counts']
        for key, expected in dict(scene_phrase_pairs=2, scenes=1, frames=64, invalid_frames=2,
                ignored_frames=1, gt_present=4, gt_absent=57, tp=3, fn=1, fp=1, tn=56,
                valid_frames=62, evaluated_frames=61, predicted_present=4).items():
            self.assertEqual(counts[key], expected, key)
        for key, expected in dict(presence_recall=.75, presence_precision=.75,
                false_positive_rate=1/57, mask_iou=(.002+.01+.05+.051)/4).items():
            self.assertAlmostEqual(overall[key]['value'], expected)
            np.testing.assert_allclose(overall[key]['ci90'], [expected, expected])
            self.assertEqual(overall[key]['bootstrap_valid_resamples'], 2000)
        low, mid, high = [result['by_gt_area'][b] for b in R.BINS]
        self.assertEqual(low['counts']['gt_present'], 1)
        self.assertEqual(low['counts']['gt_absent'], 57)
        self.assertEqual(low['counts']['ignored_frames'], 1)
        self.assertEqual(mid['counts']['gt_present'], 2)
        self.assertEqual(mid['presence_recall']['value'], .5)
        self.assertEqual(high['counts']['gt_present'], 1)
        self.assertIsNone(mid['false_positive_rate']['value'])
        self.assertIsNone(high['false_positive_rate']['ci90'])
        self.assertFalse(result['presence_go']['passed'])
        self.assertEqual(result['presence_go']['result'], 'FAIL')
        details = result['scenes'][self.scene]
        self.assertEqual(details['matched'], [dict(phrase='chair', instance_ids=[7, 9]),
                                            dict(phrase='couch', instance_ids=[12])])
        self.assertEqual(details['unmatched'], ['no such object'])
        self.assertEqual(load(self.root/'RASTERS.json'), result)

    def test_nearest_resize_uses_normalized_pixel_centers(self):
        mask = np.array([[1, 0, 0], [0, 0, 1]], bool)
        expected = np.array([[1, 1, 0, 0, 0], [0, 0, 0, 1, 1], [0, 0, 0, 1, 1]], bool)
        np.testing.assert_array_equal(R.nearest_mask(mask, (3, 5)), expected)
        np.testing.assert_array_equal(R.nearest_mask(mask, mask.shape), mask)

    def test_scene_bootstrap_pools_counts_and_repeats_whole_scenes(self):
        rows = {}
        for name, positives, tp, fp, iou in [('a', 1, 1, 1, 1.), ('b', 9, 0, 0, 0.)]:
            rows[name] = {key: R.empty_counts() for key in ('overall', *R.BINS)}
            rows[name]['overall'].update(frames=positives+1, gt_present=positives,
                gt_absent=1, tp=tp, fn=positives-tp, fp=fp, tn=1-fp, iou_sum=iou)
        result = R.summarize(rows)
        self.assertEqual(result, R.summarize(dict(reversed(list(rows.items())))))
        self.assertEqual(result['overall']['presence_recall']['value'], .1)
        self.assertEqual(result['overall']['presence_precision']['value'], .5)
        self.assertEqual(result['overall']['presence_recall']['ci90'], [0., 1.])
        self.assertEqual(result['overall']['mask_iou']['ci90'], [0., 1.])
        self.assertLess(result['overall']['presence_precision']['bootstrap_valid_resamples'], 2000)
        self.assertIsNone(result['by_gt_area']['<1%']['presence_recall']['value'])
        draws = np.random.default_rng(17).integers(0, 2, (2000, 2))
        expected = int(np.count_nonzero((draws == 0).any(1)))
        self.assertEqual(result['overall']['presence_precision']['bootstrap_valid_resamples'], expected)

    def test_heldout_union_and_tuning_exclusion(self):
        odd = next('odd'+str(i) for i in range(20)
                   if int(hashlib.sha256(('odd'+str(i)).encode()).hexdigest(), 16) % 2)
        even = next('even'+str(i) for i in range(20)
                    if not int(hashlib.sha256(('even'+str(i)).encode()).hexdigest(), 16) % 2)
        frozen, dev, vsi, vsti = [self.root/(n+'-split.json') for n in ('frozen', 'dev', 'vsi', 'vsti')]
        write(frozen, dict(tune_scenes=['tune']))
        dev.write_text('\n'.join(json.dumps(dict(scene_name=s, dataset=d))
            for s, d in [(odd, 'scannet'), (even, 'scannet'), ('non-scannet', 'arkitscenes')]))
        write(vsi, [dict(scene_name=s, dataset=d) for s, d in
                    [('bench', 'scannet'), ('tune', 'scannet'), ('other', 'arkitscenes')]])
        write(vsti, [dict(scene_name='vsti'), dict(scene_name='tune')])
        self.assertEqual(R.heldout_scenes(frozen, dev, vsi, vsti), {odd, 'bench', 'vsti'})

    def test_go_boundary_and_null_denominators(self):
        for positives, recalled, expected in [(25, 23, 'PASS'), (25, 22, 'FAIL'), (0, 0, 'FAIL')]:
            with self.subTest(positives=positives, recalled=recalled):
                case = self.root/f'go-{positives}-{recalled}'
                case.mkdir()
                export = case/'export'
                export.mkdir()
                self.inst[:] = 0
                self.inst[:positives, 0, :2] = 7
                self.valid[:] = True
                self.save_gt()
                values = copy.deepcopy(self.values)
                values['prob'][:] = 0
                values['prob'][0, :recalled] = .6
                values['frame_prob'][:] = values['prob']
                E.save_npz(export/'a.npz', self.names, values, self.audit)
                result = R.run(export, self.artifact, case/'read.json', gt_root=self.gt, **self.paths)
                self.assertEqual(result['presence_go']['result'], expected)
                if not positives:
                    self.assertIsNone(result['overall']['presence_recall']['value'])
                    self.assertIsNone(result['overall']['presence_precision']['value'])
                    self.assertIsNone(result['overall']['mask_iou']['ci90'])

    def test_rejects_anchor_mismatch(self):
        self.save_gt(indices=list(range(1, 33)))
        with self.assertRaisesRegex(ValueError, 'anchor mismatch'):
            self.run_read()
        self.assertFalse((self.root/'RASTERS.json').exists())

    def test_rejects_tau_artifact_missing_and_duplicate_exports(self):
        for field in ('tau', 'artifact', 'missing', 'duplicate'):
            with self.subTest(field=field):
                export = self.root/(field+'-export')
                export.mkdir()
                audit = copy.deepcopy(self.audit)
                if field == 'tau':
                    audit['tau'] = .5
                if field == 'artifact':
                    audit['mdg_artifact']['meta']['sha256'] = '0'*64
                if field == 'missing':
                    audit['entry']['scene'] = 'scannet/not-heldout'
                E.save_npz(export/'a.npz', self.names, self.values, audit)
                if field == 'duplicate':
                    E.save_npz(export/'b.npz', self.names, self.values, audit)
                with self.assertRaises(ValueError):
                    R.run(export, self.artifact, self.root/(field+'-out.json'), gt_root=self.gt, **self.paths)

    def test_native_export_journal_and_cli(self):
        entry = dict(self.entry, video_rel='scannet/'+self.scene+'.mp4', fps=24., total_num_frames=40,
            frames=[dict(index=k) for k in range(32)], anchor_pixel_sha256='a'*64,
            duplicate_pixel_sha256='b'*64)
        manifest = self.root/'manifest.json'
        write(manifest, [entry])
        key = E.selection_id(entry)
        export = self.root/'native'
        export.mkdir()
        request = dict(schema='mdg-export-v1', manifest=file_pin(manifest), mdg_meta=file_pin(self.meta),
            tau=.6, world=1, groups={key: self.names})
        write(export/'run.json', request)
        audit = dict(self.audit, entry=entry, binding=digest(request), selection=key)
        npz = export/(key+'.npz')
        E.save_npz(npz, self.names, self.values, audit)
        (export/'export-0.jsonl').write_text(json.dumps(dict(selection=key, binding=digest(request),
            rank=0, npz=file_pin(npz)))+'\n')
        patches = dict(GT=self.gt, FROZEN=self.paths['frozen'], DEV=self.paths['dev'],
                       VSI=self.paths['vsi'], VSTI=self.paths['vsti'])
        with mock.patch.multiple(R, **patches), mock.patch('builtins.print') as printed:
            R.main(['--export', str(export), '--artifact', str(self.artifact),
                    '--out', str(self.root/'cli.json'), '--scenes', 'heldout'])
        result = load(self.root/'cli.json')
        self.assertEqual(result['overall']['presence_recall']['value'], .75)
        printed.assert_called_once_with('Presence GO:', 'FAIL', .75)
        with self.assertRaises(FileExistsError):
            R.run(export, self.artifact, self.root/'cli.json', gt_root=self.gt, **self.paths)

    def test_real_label_matching_and_non32_rejection(self):
        match = R.label_matcher()
        self.assertEqual(match('the red chair', ['chair', 'sofa']), ['chair'])
        self.assertEqual(match('couch', ['sofa']), ['sofa'])
        with (self.gt/(self.scene+'.npz')).open('wb') as stream:
            np.savez(stream, inst=self.inst[:2], ids=self.ids, labels=self.labels,
                     valid=self.valid[:2], frame_indices=[0, 1])
        with self.assertRaisesRegex(ValueError, 'Invalid GT raster'):
            self.run_read()

    def test_zero_instance_id_and_nonempty_union_below_individual_thresholds(self):
        self.ids = np.array([0, 9, 12])
        self.inst[self.inst == 7] = 0
        self.inst[:] = -1
        self.inst[0, 0, :2] = [0, 9]
        self.valid[:] = True
        self.save_gt()
        result = self.run_read()
        self.assertEqual(result['overall']['counts']['gt_present'], 1)
        self.assertEqual(result['overall']['presence_recall']['value'], 1.)
        self.assertEqual(result['scenes'][self.scene]['matched'][0]['instance_ids'], [0, 9])


if __name__ == '__main__':
    unittest.main()
