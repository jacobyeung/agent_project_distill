"""Retained synthetic anchors, fake MDG export and reference scorer/W10 parity."""
import importlib.util
from contextlib import nullcontext
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
from PIL import Image
import torch

from student_pilot import mdg_eval as E
from student_pilot.p3_provenance import file_pin, load, write


class FakeHead(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.video_calls = 0

    def encode_video(self, taps, vit, pixels, grid):
        self.video_calls += 1
        return {}

    def forward(self, video, query, phrase, phrase_mask):
        q = query.shape[0]
        masks = torch.full((q, 32, 8, 9), -1.)
        masks[:, :, 2:6, 2:7] = 1.
        frame = torch.full((q, 32), 3.)
        frame[query[:, 0, 0] > 0] = -3.
        return [dict(mask_logit=masks, clip_logit=torch.full((q,), 3.), frame_logit=frame,
                     iou=torch.full((q, 32), .8))]

    def decode(self, out):
        q = len(out['clip_logit'])
        mask = out['mask_logit'] > 0
        return dict(prob=out['clip_logit'].sigmoid()[:, None]*out['frame_logit'].sigmoid(),
                    mask=mask, uv=torch.full((q, 32, 2), 500), iou=out['iou'], area=mask.sum((-1, -2)))


class MDGEval(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='mdg-eval-', dir=os.environ['LANE_TEST_OUTPUT']))
        self.png = self.root/'png'
        self.png.mkdir()
        frames, arrays = [], []
        for k in range(32):
            a = np.full((12, 18, 3), k, np.uint8)
            path = self.png/f'{k}.png'
            Image.fromarray(a).save(path, compress_level=1)
            frames.append(dict(path=path.name, sha256=E.sha256(path), index=k))
            arrays.append(a)
        a = np.stack(arrays)
        self.entry = dict(scene='scannet/scene0000_00', video_rel='scannet/scene0000_00.mp4',
            frame_indices=list(range(32)), fps=24., total_num_frames=40, frames=frames,
            anchor_pixel_sha256=E.pixel_digest(a), duplicate_pixel_sha256=E.pixel_digest(np.repeat(a, 2, axis=0)))
        self.manifest = self.root/'A_MANIFEST.json'
        write(self.manifest, dict(selections=[self.entry]))
        self.items = [dict(id=name, scene=self.entry['scene'], obj=obj, frame=k,
            video_rel=self.entry['video_rel'], frame_indices=list(range(32)), fps=24., total_num_frames=40,
            source_index=k-1) for name, obj, k in [('a', ' Chair ', 3), ('b', 'chair', 4), ('c', 'missing', 1)]]
        self.membership = self.root/'membership.json'
        write(self.membership, dict(items=self.items))
        self.absent = self.root/'absent.json'
        write(self.absent, dict(items=[dict(id='absent', scene=self.entry['scene'], obj='never', frame=8)]))
        self.cfg = self.root/'cfg.json'
        write(self.cfg, {})
        self.artifact = self.root/'artifact.json'
        write(self.artifact, dict(schema='synthetic-cpu-fixture'))
        self.bundle = self.root/'BUNDLE.json'
        write(self.bundle, dict(schema='mdg-t0-bundle-v1', fixture=True))
        self.mdg = self.root/'mdg'
        self.mdg.mkdir()
        write(self.mdg/'mdg.json', dict(base_artifact=file_pin(self.artifact), tau=.5))
        (self.mdg/'mdg.pt').write_bytes(b'fake-head')
        self.head = FakeHead()
        self.model = SimpleNamespace(mdg_head=self.head)
        self.prefills, self.suffixes = [], []
        self.export = self.root/'export'

    def capture(self, model, batch):
        self.prefills.append(batch)
        return SimpleNamespace(taps=[], vit=[], pixels=torch.zeros(32, 3, 32, 32), grid=(1, 1))

    def suffix(self, model, prefix, names, chunk):
        self.suffixes.append(names)
        query = torch.zeros(len(names), 2, 4)
        query[:, 0, 0] = torch.tensor([name == 'never' for name in names])
        return SimpleNamespace(query=query, phrase=torch.zeros(len(names), 8, 2, 4),
                               phrase_mask=torch.ones(len(names), 8, dtype=torch.bool))

    def run_export(self, rank=0, world=1):
        from student_pilot import carrier_c1_canary as C, mdg_stream
        features = SimpleNamespace(capture_prefix=self.capture, suffix_states=self.suffix)
        batch = dict(input_ids=torch.tensor([[2, 3]]))
        with mock.patch.object(E, 'load_runtime', return_value=(self.model, SimpleNamespace(), {})), \
             mock.patch.object(C, 'prompt_batch', return_value=batch), \
             mock.patch.object(mdg_stream, 'stream_suffix_states',
                 side_effect=lambda model, prefix, batch, names, chunk: self.suffix(model, prefix, names, chunk)), \
             mock.patch.dict('sys.modules', {'student_pilot.mdg_features': features}):
            return E.run_export(self.manifest, self.png, [self.membership, self.absent], self.mdg,
                self.cfg, file_pin(self.artifact), self.export, rank, world, t0_bundle=self.bundle)

    def test_exact_trainer_row_pixels_and_metadata(self):
        row, audit = E.trainer_row(self.entry, self.png, 'example')
        from student_pilot.grounding_train import QUESTION
        data = row['student_input']
        self.assertEqual(data['question'], QUESTION)
        self.assertEqual(data['timestamps'], [i/24 for i in range(32)])
        self.assertEqual(data['fps'], 24.)
        self.assertEqual(data['total_num_frames'], 40)
        self.assertEqual(audit['anchor_pixel_sha256'], self.entry['anchor_pixel_sha256'])
        self.assertEqual(data['frames'][0], file_pin(self.png/'0.png'))
        bad = dict(self.entry, anchor_pixel_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'pixels'):
            E.trainer_row(bad, self.png, 'bad')
        bad = dict(self.entry, duplicate_pixel_sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'pixels'):
            E.trainer_row(bad, self.png, 'bad')

    def test_export_union_one_prefix_resume_and_packed_masks(self):
        result = self.run_export()
        self.assertEqual(result['completed'], 1)
        self.assertEqual(self.suffixes, [['chair', 'missing', 'never']])
        self.assertEqual(len(self.prefills), 1)
        self.assertEqual(self.head.video_calls, 1)
        self.run_export()
        self.assertEqual(len(self.prefills), 1)
        exports = E.Exports(self.export)
        names, values, audit = exports.get(E.selection_id(self.entry))
        self.assertEqual(values['mask'].shape, (3, 32, 8, 9))
        self.assertTrue(values['mask'][0, 0, 3, 3])
        self.assertFalse(values['mask'][0, 0, 0, 0])
        self.assertEqual(audit['t0_artifact'], file_pin(self.artifact))
        self.assertEqual(audit['t0_bundle_sha256'], E.sha256(self.bundle))
        self.assertGreater(audit['seconds'], 0)
        with np.load(self.export/(E.selection_id(self.entry)+'.npz')) as z:
            self.assertEqual(z['masks'].shape, (3, 32, 8, 2))
        self.assertEqual(names, ['chair', 'missing', 'never'])

    def test_standalone_runtime_receives_pins_and_binds_processor(self):
        processor = SimpleNamespace(tokenizer=object())
        self.model.mdg_runtime_report = dict(bundle_sha256=E.sha256(self.bundle))
        runtime = SimpleNamespace(load_runtime=mock.Mock(return_value=(self.model, processor, {})))
        features = SimpleNamespace(bind_processor=mock.Mock())
        meta = load(self.mdg/'mdg.json')
        meta['base_artifact']['path'] = '/relocated/original/artifact.json'
        head_module = SimpleNamespace(load_artifact=mock.Mock(return_value=(self.head, meta)))
        with mock.patch.dict('sys.modules', {'student_pilot.mdg_runtime': runtime,
                'student_pilot.mdg_features': features, 'student_pilot.mask_grounding_head': head_module}):
            E.load_runtime(file_pin(self.cfg), file_pin(self.artifact), self.mdg, 'cpu', file_pin(self.bundle))
        cfg = runtime.load_runtime.call_args.args[0]
        self.assertEqual(cfg['c1_config'], file_pin(self.cfg))
        self.assertEqual(cfg['bundle'], file_pin(self.bundle))
        features.bind_processor.assert_called_once_with(self.model, processor)

    def test_rank_coverage_and_changed_world_refused(self):
        self.run_export(1, 2)
        with self.assertRaisesRegex(ValueError, 'Missing export shard'):
            E.Exports(self.export)
        self.run_export(0, 2)
        E.Exports(self.export)
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.run_export(0, 1)

    def test_changed_png_and_config_fail_closed(self):
        Image.fromarray(np.zeros((12, 18, 3), np.uint8)).save(self.png/'1.png')
        with self.assertRaisesRegex(ValueError, 'pinned input'):
            self.run_export()
        self.assertFalse((self.export/'export-0.jsonl').exists())

    def test_record_schema_threshold_and_reference_parser(self):
        self.run_export()
        exports = E.Exports(self.export)
        accepted = E.record_for(self.items[0], exports)
        absent = E.record_for(load(self.absent)['items'][0], exports)
        self.assertEqual(json.loads(accepted['raw_generation']), dict(point_2d=[500, 500]))
        self.assertEqual(json.loads(absent['raw_generation']), dict(point_2d=None))
        expected = E.GH.record_for(E.task_for(self.items[0], self.entry), accepted['mdg'], .5,
                                  exports.binding, 0, {})
        for k in ('key', 'example_id', 'source_index', 'num_frames', 'num_viewpoints', 'response_text'):
            self.assertEqual(accepted[k], expected[k])
        scorer = E.score_tools()
        self.assertFalse(scorer.parse_output(accepted['raw_generation'])['parse_failed'])
        self.assertTrue(scorer.parse_output(absent['raw_generation'])['none'])

    def test_w10_top1_lifting_rle_and_native_resize(self):
        self.run_export()
        out = self.root/'w10-source'
        E.run_w10(self.export, self.membership, out)
        E.run_w10(self.export, self.membership, out)
        ground = load(out/'ground/ground_mdg_t0m800top1x/scannet__scene0000_00.json')['out']
        self.assertIsNone(json.loads(ground['a'])[0]['point_2d'])
        self.assertEqual(json.loads(ground['b'])[0]['point_2d'], [500, 500])
        lift = load(out/'lifting/mdg_t0m800/scannet__scene0000_00.json')
        slots = lift['objects']['chair']['accepted_slots']
        self.assertEqual(len(slots), 32)
        self.assertEqual(lift['objects']['chair']['first_seen_slot'], 0)
        common = E.module_at('_mdg_test_sam_common', E.SAM/'common.py')
        rec = slots['0']
        mask = common.rle_decode(rec['instances'][0]['mask'])
        self.assertEqual(mask.shape, (12, 18))
        self.assertEqual(common.rle_encode(mask), rec['instances'][0]['mask'])
        self.assertEqual(rec['instances'][0]['box'], [4, 3, 14, 9])
        self.assertEqual(lift['objects']['never']['accepted_slots'], {})

    def test_selection_ambiguity_and_identity_checks(self):
        entries = E.manifest_entries(self.manifest)
        alternate = dict(self.entry, fps=30.)
        entries[E.selection_id(alternate)] = alternate
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            E.selection_for(load(self.absent)['items'][0], entries)
        self.assertEqual(E.selection_for(self.items[0], entries), E.selection_id(self.entry))
        bad = dict(self.items[0], source_index=99)
        with self.assertRaises(ValueError):
            E.selection_for(bad, entries)

    def test_score_eroded_masks_area_bins_absence_and_paired_ci(self):
        score = E.score_tools()
        mask = np.zeros((100, 100), bool)
        mask[30:70, 30:70] = True
        gt = SimpleNamespace(gt=SimpleNamespace(valid=np.ones(32, bool)),
            masks=lambda obj, k: [(1, mask)] if obj.strip().lower() == 'chair' else [])
        self.run_export()
        exports = E.Exports(self.export)
        rows = [E.record_for(item, exports) for item in self.items]
        with mock.patch.object(score, 'programs', return_value=None), mock.patch.object(score, 'ground', return_value=gt):
            scored = E.score_records(self.items, rows, score, dict(scannet=self.root), self.cfg)
        self.assertEqual([r['visible'] for r in scored], [True, True, False])
        self.assertEqual(scored[0]['area_bin'], '>5%')
        self.assertEqual(scored[0]['inside'], 1.)
        baseline = {r['example_id']: dict(r, inside=0.) for r in scored}
        absent = [E.record_for(load(self.absent)['items'][0], exports)]
        result = E.report_pointing(scored, baseline, absent, 100)
        self.assertEqual(result['all']['paired_in_mask_vs_t0']['ci90'], [1., 1.])
        self.assertEqual(result['scene_absent_fp']['value'], 0.)
        self.assertEqual(result['datasets']['arkit']['in_mask']['n'], 0)
        with self.assertRaisesRegex(ValueError, 'coverage'):
            E.report_pointing(scored, {}, absent, 100)

    def test_export_tampering_and_unjournaled_recovery(self):
        self.run_export()
        journal = self.export/'export-0.jsonl'
        saved = journal.read_text()
        journal.rename(self.export/'retained-journal.jsonl')
        self.run_export()
        self.assertEqual(journal.read_text(), saved)
        self.assertEqual(len(self.prefills), 1)
        path = self.export/(E.selection_id(self.entry)+'.npz')
        with path.open('ab') as stream:
            stream.write(b'tampered')
        with self.assertRaisesRegex(ValueError, 'pinned input'):
            E.Exports(self.export).get(E.selection_id(self.entry))

    def test_runner_rejects_reference_output_and_changed_interfaces(self):
        path = Path(__file__).resolve().parents[2]/'w10_mdg/run.py'
        runner = E.module_at('_mdg_w10_runner', path)
        with self.assertRaisesRegex(ValueError, 'under'):
            runner.owned_output(runner.REFERENCE/'out/mdg')
        with self.assertRaisesRegex(RuntimeError, 'interface'):
            runner.replace_once('changed', 'old', 'new')
        self.assertEqual(runner.replace_once('old', 'old', 'new'), 'new')

    def test_pointing_phase_writes_records_ground_and_report(self):
        membership = load(self.membership)
        membership['sources'] = dict(programs=E.sha256(self.cfg))
        self.membership.write_text(json.dumps(membership))
        baseline = self.root/'baseline.json'
        mask = np.zeros((100, 100), bool)
        mask[30:70, 30:70] = True
        score = E.score_tools()
        gt = SimpleNamespace(gt=SimpleNamespace(valid=np.ones(32, bool)),
            masks=lambda obj, k: [(1, mask)] if obj.strip().lower() == 'chair' else [])
        self.run_export()
        exports = E.Exports(self.export)
        rows = [E.record_for(item, exports) for item in self.items]
        with mock.patch.object(score, 'programs', return_value=None), mock.patch.object(score, 'ground', return_value=gt):
            scored = E.score_records(self.items, rows, score, dict(scannet=self.root), self.cfg)
            base = [dict(r, membership_id=r['example_id'], variant='A', example_id=r['example_id']+':A') for r in scored]
            write(baseline, dict(models=dict(t0m800=dict(conditions=dict(markers_on=dict(items=base))))))
            with mock.patch.object(E, 'score_tools', return_value=score), \
                 mock.patch.object(score, 'validate_pointing'):
                out = self.root/'pointing'
                result = E.run_pointing(self.export, self.membership, self.membership, self.absent, out,
                    baseline=baseline, gt_roots=dict(scannet=self.root), programs_path=self.cfg, samples=100)
                again = E.run_pointing(self.export, self.membership, self.membership, self.absent, out,
                    baseline=baseline, gt_roots=dict(scannet=self.root), programs_path=self.cfg, samples=100)
        self.assertEqual(result, again)
        self.assertEqual(result['all']['paired_in_mask_vs_t0']['value'], 0.)
        self.assertEqual(result['baseline'], file_pin(baseline))
        ground = load(out/'ground/ground_mdg_t0m800/scannet__scene0000_00.json')
        self.assertEqual(set(ground['out']), {'a', 'b', 'c'})
        self.assertEqual(len((out/'scene_absent.jsonl').read_text().splitlines()), 1)

    def test_z_runner_native_context_uses_only_mdg_source(self):
        self.run_export()
        inputs = self.root/'w10-source'
        E.run_w10(self.export, self.membership, inputs)
        runner = E.module_at('_mdg_w10_native_runner', Path(__file__).resolve().parents[2]/'w10_mdg/run.py')
        output = Path(tempfile.mkdtemp(prefix='native-context-', dir=runner.HERE))
        state = runner.setup('mdg', output, inputs)
        geometry = SimpleNamespace(dense=lambda *a: None, cam=lambda k: (np.eye(3), np.zeros(3)),
                                   fov_of=lambda k: np.array([1., 1.]))
        def npz(path, **kwargs):
            if 'heads_g3s64' in str(path):
                return nullcontext(dict(scale=np.array(1.), anchor_frame_indices=np.arange(32)))
            return nullcontext(dict(depth_lo=np.ones((32, 12, 18)), frame_indices=np.arange(32),
                                    anchor_slots=np.arange(32)))
        items = {self.entry['scene']: {('chair', 4, 'point', ''): self.items[1]}}
        with mock.patch.object(state.MP.PR, 'load_heads', return_value=geometry), \
             mock.patch.object(state.MP.np, 'load', side_effect=npz):
            context = state.MP.MaskContext('scene0000_00', 'sam3mask', items)
            frame = context.frame('chair', 4)
            self.assertGreater(len(frame['points']), 0)
            self.assertEqual(context.support('chair', 4, 1.), list(range(1, 33)))
            self.assertEqual(len(frame['scores']), 1)
            self.assertEqual(context.ground.get('chair', 4, 'point'), [[500., 500.]])
            self.assertTrue(all(str(inputs) in str(p) for p in context.provenance[2:]))
            def wrong_npz(path, **kwargs):
                if 'heads_g3s64' in str(path):
                    return nullcontext(dict(scale=np.array(1.), anchor_frame_indices=np.arange(32)+1))
                return npz(path, **kwargs)
            with mock.patch.object(state.MP.np, 'load', side_effect=wrong_npz):
                with self.assertRaisesRegex(ValueError, 'anchor mismatch'):
                    state.MP.MaskContext('scene0000_00', 'sam3mask', items)
            path = inputs/'lifting/mdg_t0m800/scannet__scene0000_00.json'
            with path.open('a') as stream:
                stream.write(' ')
            with self.assertRaisesRegex(ValueError, 'source file changed'):
                state.MP.MaskContext('scene0000_00', 'sam3mask', items)

    def test_zz_runner_uses_native_tuning_grid_and_separate_ablation(self):
        self.run_export()
        inputs = self.root/'w10-source'
        E.run_w10(self.export, self.membership, inputs)
        runner = E.module_at('_mdg_w10_tune_runner', Path(__file__).resolve().parents[2]/'w10_mdg/run.py')
        output = Path(tempfile.mkdtemp(prefix='synthetic-tune-', dir=runner.HERE))
        state = runner.setup('mdg', output, inputs)
        ref = load(runner.REFERENCE/'mask_frozen.json')
        qs = [dict(id=f'{scene}-{i}', scene_name=scene, question_type='synthetic', ground_truth='A')
              for scene in ref['tune_scenes'] for i in range(11)]
        direct = {('dev', q['id']): dict(score=.2) for q in qs}
        context = SimpleNamespace(provenance=[inputs/'source.json'], frames={})
        with mock.patch.object(state.ME, 'dev_rows', return_value=qs), \
             mock.patch.object(state.ME, 'direct_rows', return_value=direct), \
             mock.patch.object(state.ME.AE, 'item_groups', return_value={}), \
             mock.patch.object(state.ME, 'MaskContext', return_value=context), \
             mock.patch.object(state.ME, 'predict', return_value=dict(err=None, pred='A')), \
             mock.patch.object(state.ME.T, 'score', return_value=1.), \
             mock.patch.object(state.ME, 'rejection', side_effect=lambda r, c, m, f, radius: [] if (m, f) == (.9, 1) else ['reject']), \
             mock.patch.object(state.ME, 'bench_rows', side_effect=AssertionError('held-out read during tune')):
            with mock.patch('builtins.print'):
                state.ME.tune()
        frozen = state.ME.frozen_config()
        self.assertEqual((frozen['m'], frozen['f'], frozen['n']), (.9, 1, 341))
        self.assertEqual(len(frozen['grid']), 12)
        self.assertEqual(frozen['tune_scenes'], ref['tune_scenes'])
        self.assertEqual(frozen['radius_m'], ref['radius_m'])
        self.assertIn('single MDG union mask', frozen['ambiguity'])
        self.assertTrue(frozen['own_ground'].startswith(str(inputs)))
        ablation_out = Path(tempfile.mkdtemp(prefix='synthetic-params-', dir=runner.HERE))
        state = runner.setup('mdg', ablation_out, inputs)
        with mock.patch.object(state.ME, 'dev_rows', return_value=qs):
            runner.freeze_ablation(state)
        ablation = load(state.ME.FROZEN)
        self.assertEqual((ablation['m'], ablation['f']), (.9, 1))
        self.assertIsNone(ablation['selection'])
        self.assertEqual(ablation['grid'], [])
        with self.assertRaises(FileExistsError):
            runner.freeze_ablation(state)


if __name__ == '__main__':
    unittest.main()
