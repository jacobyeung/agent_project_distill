"""Clip grouping, durable resume and unchanged evalx scorer compatibility."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

from student_pilot import grounding_eval as evaluation
from student_pilot import grounding_features as features
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_grounding_decode import FakeGH, GroundTokenizer


class EvalModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = torch.nn.Embedding(64, 32)
        self.grounding_head, self.grounding_meta = FakeGH(), dict(tau=.6)
        self.config = SimpleNamespace(vision_config=SimpleNamespace(patch_size=2, spatial_merge_size=2))

    def get_input_embeddings(self):
        return self.embedding


class GroundingEval(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='gh-eval-', dir=os.environ['LANE_TEST_OUTPUT']))
        self.pm = evaluation.pointing_module()
        self.membership = dict(items=[dict(id=name, scene='scannet/scene0000_00', obj=obj, frame=k,
            frame_indices=list(range(offset, offset+32)), source_index=k-1+offset, fps=30., total_num_frames=100,
            video_rel='clip.mp4') for name, obj, k, offset in
            [('a', 'chair', 3, 0), ('b', 'missing', 1, 0), ('c', 'chair', 4, 1)]])
        write(self.root/'membership.json', self.membership)
        self.cfg = dict(carrier_placement='append_after_temporal_group_video_tokens_v1', frame_layout='duplicate',
                        frame_markers=True, training_mode='final', depth_enabled=True)
        write(self.root/'cfg.json', self.cfg)
        write(self.root/'artifact.json', dict(schema='synthetic-cpu-fixture'))
        self.gh = self.root/'gh'
        self.gh.mkdir()
        write(self.gh/'gh.json', dict(tau=.6))
        (self.gh/'gh.pt').write_bytes(b'synthetic-cpu-fixture')
        self.model, self.processor = EvalModel(), SimpleNamespace(tokenizer=GroundTokenizer())
        self.prefills, self.decodes = [], []

    def decode_row(self, task, cache):
        self.decodes.append(task)
        return dict(qid=task['example_id'], student_input={}), dict(anchor_pixel_sha256='a'*64,
                                                                 duplicate_pixel_sha256='b'*64)

    def capture(self, model, batch):
        self.prefills.append(batch)
        return features.ClipFeatures([torch.zeros(32, 1, 32)]*3, torch.zeros(32, 2, 2, 32), (1, 1),
                                     torch.zeros(1, 2, 32))

    def run_rank(self, rank=0, world=1):
        from student_pilot import carrier_c1_canary
        batch = dict(input_ids=torch.tensor([[2, 3]]), attention_mask=torch.ones(1, 2, dtype=torch.long))
        with mock.patch.object(evaluation, 'load_runtime', return_value=(self.model, self.processor)), \
             mock.patch.object(self.pm, 'trainer_row', side_effect=self.decode_row), \
             mock.patch.object(carrier_c1_canary, 'prompt_batch', return_value=batch), \
             mock.patch.object(features, 'capture', side_effect=self.capture):
            return evaluation.run_worker(self.root/'membership.json', self.gh, self.root/'cfg.json',
                file_pin(self.root/'artifact.json'), self.root/'frames', self.root/'out', rank, world, device='cpu')

    def test_group_one_prefill_and_resume(self):
        result = self.run_rank()
        self.assertEqual(result['completed'], 3)
        self.assertEqual(len(self.prefills), 2)
        self.assertEqual(len(self.decodes), 2)
        self.assertEqual(self.model.grounding_head.video_calls, 2)
        self.assertEqual(self.model.grounding_head.query_calls, 2)
        self.run_rank()
        self.assertEqual(len(self.prefills), 2)
        summary = evaluation.merge(self.root/'out', 1)
        self.assertEqual(summary['completed'], 3)
        self.assertFalse(summary['parity_pass'])
        rows = [json.loads(line) for line in (self.root/'out/per-item.jsonl').read_text().splitlines()]
        self.assertEqual([len(row['gh']['prob']) for row in rows], [32]*3)
        self.assertEqual([len(row['gh']['uv']) for row in rows], [32]*3)
        self.assertEqual(rows[0]['raw_generation'], '{"point_2d": [412, 550]}')
        self.assertEqual(rows[1]['raw_generation'], '{"point_2d": null}')
        self.assertEqual(evaluation.merge(self.root/'out', 1), summary)

    def test_actual_scorer_accepts_record_schema_and_parses(self):
        self.run_rank()
        summary = evaluation.merge(self.root/'out', 1)
        path = Path('/scratch/jjyeung/orch_cd/evalx/work/aws_v/local/score_pointing_markers.py')
        spec = importlib.util.spec_from_file_location('gh_marker_scorer', path)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        scorer = adapter.load_scorer()
        rows = scorer.read_records(self.root/'out/per-item.jsonl')
        for row in rows:
            self.assertFalse(scorer.parse_output(row['raw_generation'])['parse_failed'])
        gg = SimpleNamespace(gt=SimpleNamespace(valid=[True]*32),
            masks=lambda obj, k: [] if obj == 'missing' else [(1, np.ones((10, 10), dtype=bool))])
        with mock.patch.object(scorer, 'validate_pointing'), mock.patch.object(scorer, 'programs'), \
             mock.patch.object(scorer, 'ground', return_value=gg):
            result = adapter.score(rows, self.membership, summary, scorer)
        cell = result['models']['gh']['conditions']['markers_on']
        self.assertTrue(cell['variants']['A']['complete'])
        self.assertEqual(cell['variants']['A']['malformed_rate'], 0.)
        self.assertEqual(cell['variants']['A']['inside_rate'], 1.)
        self.assertEqual(cell['variants']['A']['explicit_none_rate'], 1.)

    def test_group_sharding_and_missing_merge(self):
        self.run_rank(0, 2)
        self.assertEqual(len(self.prefills), 1)
        with self.assertRaisesRegex(ValueError, 'Missing or failed'):
            evaluation.merge(self.root/'out', 2)
        self.run_rank(1, 2)
        self.assertEqual(len(self.prefills), 2)
        self.assertEqual(evaluation.merge(self.root/'out', 2)['completed'], 3)
        with self.assertRaisesRegex(ValueError, 'world differs'):
            evaluation.merge(self.root/'out', 1)

    def test_failed_items_resume_and_changed_binding_refuses(self):
        with mock.patch.object(evaluation, 'predict_group', side_effect=ValueError('synthetic failure')):
            self.assertEqual(self.run_rank()['completed'], 0)
        with self.assertRaisesRegex(ValueError, 'Missing or failed'):
            evaluation.merge(self.root/'out', 1)
        self.assertEqual(self.run_rank()['completed'], 3)
        self.assertEqual(len(self.prefills), 2)
        (self.gh/'gh.json').write_text('{"tau": 0.9}')
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            self.run_rank()

    def test_to_ground_harness_format(self):
        self.run_rank()
        evaluation.merge(self.root/'out', 1)
        result = evaluation.to_ground(self.root/'out/per-item.jsonl', self.root/'membership.json',
                                      'gh_t0m800', self.root/'ground')
        self.assertEqual(result['items'], 3)
        payload = load(Path(result['output'])/'scannet__scene0000_00.json')
        self.assertEqual(payload, dict(scene='scannet/scene0000_00',
            out=dict(a='{"point_2d": [412, 550]}', b='{"point_2d": null}', c='{"point_2d": [412, 550]}')))
        with self.assertRaises(ValueError):
            evaluation.to_ground(self.root/'out/per-item.jsonl', self.root/'membership.json', '../unsafe', self.root)

    def test_selection_and_metadata_guards(self):
        tasks = evaluation.tasks_for(self.membership, self.pm)
        for rank, world in ((0, 0), (-1, 2), (2, 2)):
            with self.assertRaisesRegex(ValueError, 'rank/world'):
                evaluation.group_tasks(tasks, rank, world)
        tasks[1]['fps'] = 15.
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            evaluation.group_tasks(tasks, 0, 1)
        self.membership['items'][0]['frame'] = 0
        with self.assertRaisesRegex(ValueError, 'Invalid pointing'):
            evaluation.tasks_for(self.membership, self.pm)

    def test_runtime_uses_routed_loaders_and_binds_gh_to_t0(self):
        from student_pilot import carrier_c1_run, grounding_head
        pin = file_pin(self.root/'artifact.json')
        cfg, receipt, manifest = dict(base_identity='tiny-base'), dict(kind='fixture'), dict(root='fixture')
        meta = dict(base_artifact=pin, tau=.6)
        gh = FakeGH()
        with mock.patch.object(carrier_c1_run, 'prepared', return_value=(receipt, manifest)) as prep, \
             mock.patch.object(carrier_c1_run, 'processor_for_receipt', return_value=self.processor) as proc, \
             mock.patch.object(carrier_c1_run, 'load_model', return_value=self.model) as model_loader, \
             mock.patch.object(carrier_c1_run, 'load_artifact', return_value=cfg) as artifact_loader, \
             mock.patch.object(grounding_head, 'load_artifact', return_value=(gh, meta)) as gh_loader:
            model, processor = evaluation.load_runtime(cfg, pin, self.gh, 'cpu')
            prep.assert_called_once_with(cfg, admission=True)
            proc.assert_called_once_with(manifest, receipt)
            model_loader.assert_called_once_with(manifest, receipt, self.processor)
            artifact_loader.assert_called_once_with(self.model, pin)
            gh_loader.assert_called_once_with(self.gh)
            self.assertIs(model.grounding_head, gh)
            self.assertIs(model.grounding_tokenizer, processor.tokenizer)
            self.assertFalse(model.training)
            self.assertFalse(any(p.requires_grad for p in model.parameters()))
            meta['base_artifact'] = dict(path=pin['path'], sha256='0'*64)
            with self.assertRaisesRegex(ValueError, 'another T0 artifact'):
                evaluation.load_runtime(cfg, pin, self.gh, 'cpu')


if __name__ == '__main__':
    unittest.main()
