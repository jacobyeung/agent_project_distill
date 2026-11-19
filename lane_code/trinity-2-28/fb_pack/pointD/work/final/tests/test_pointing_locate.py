"""CPU fixtures for the pinned Locate rebuild and loss decision boundary."""
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import torch

from student_pilot import carrier_c1_data as data, carrier_c1_run as run
from student_pilot import pointing_locate as locate
from student_pilot.p3_provenance import file_pin, write


def fixture(root):
    Image.new('RGB', (32, 24), (20, 30, 40)).save(root/'rgb.png')
    visible = np.zeros((24, 32), bool)
    visible[4:18, 6:23] = True
    tiny = np.zeros_like(visible); tiny[1, 1] = True
    np.savez(root/'masks.npz', visible=visible, absent=np.zeros_like(visible), tiny=tiny)
    frame, mask = file_pin(root/'rgb.png'), file_pin(root/'masks.npz')
    rows = []
    for index, (label, key, kind) in enumerate((('chair', 'visible', 'gt_instance_mask'),
            ('lamp', 'absent', 'gt_absent'), ('3d printer', 'visible', 'gt_instance_mask'),
            ('table', 'tiny', 'gt_instance_mask'))):
        rows.append(dict(qid=f'fixture-{index}', dataset='d1', scene='scene_test',
            student_input=dict(frames=[frame]*32, frame_indices=list(range(32)),
                question=f'Point to the {label} in frame 12. If there is no {label} in frame 12, output null.',
                options=[]), pointing=dict(label=label, kind=kind, frame=12, rgb_sha256=frame['sha256'],
                instance_id=index, key=key, mask=mask), target='ignored source text'))
    source = root/'rows.jsonl'
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    write(root/'division.json', dict(schema='diagnostic-whole-scene-division-v1', training_only=True,
        train_scenes=['d1/scene_test'], heldout_scenes=['d1/held']))
    return rows, file_pin(source), file_pin(root/'division.json')


def saved(receipt):
    with sqlite3.connect(Path(receipt['database']['path']).as_uri()+'?mode=ro', uri=True) as conn:
        return [json.loads(raw) for raw, in conn.execute('SELECT row FROM rows ORDER BY i')]


class LocateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='pointing_locate_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.rows, self.source, self.division = fixture(self.root)

    def build(self, name, rule=None, **kwargs):
        return data.build_stream(self.source, self.division, self.root/name, 'pointing',
                                 pointing_locate=rule, **kwargs)

    def test_after_mask_rebuild_preserves_answers_and_filters_bad_masks(self):
        plain = self.build('plain', ground_target_filter=True)
        marked = self.build('marked', locate.RULE_PIN, ground_target_filter=True)
        self.assertNotIn('pointing_locate', plain)
        self.assertEqual(marked['pointing_locate'], locate.RULE_PIN)
        self.assertEqual(plain['target_filter'], marked['target_filter'])
        self.assertEqual(marked['count'], 3)
        for before, after in zip(saved(plain), saved(marked)):
            answer = before['target'].split('</think>\n\n')[1]
            self.assertEqual(after['target'], locate.render(before, answer))
            self.assertEqual(after, {**before, 'target': after['target']})
            locate.assert_target(after)
        locate.assert_store(marked, locate.RULE_PIN)

    def test_native_receipt_rebuild_keeps_locate(self):
        source = self.build('source', ground_target_filter=True)
        receipt = data.build_stream(file_pin(self.root/'source/receipt.json'), self.division,
            self.root/'rebuilt', 'pointing', source_receipt=True, ground_target_filter=True,
            pointing_locate=locate.RULE_PIN)
        again = data.build_stream(file_pin(self.root/'rebuilt/receipt.json'), self.division,
            self.root/'again', 'pointing', source_receipt=True, ground_target_filter=True,
            pointing_locate=locate.RULE_PIN)
        self.assertEqual(saved(receipt), saved(again))
        self.assertEqual(receipt['count'], source['count'])
        locate.assert_store(again, locate.RULE_PIN)

    def test_exact_labels_including_digits_and_null_sentence(self):
        rows = saved(self.build('marked', locate.RULE_PIN))
        self.assertEqual(rows[1]['target'], '<think>\nLocate the lamp in frame 12: it is not visible in that frame.\n</think>\n\n{"point_2d": null}')
        self.assertIn('Locate the 3d printer in frame 12.\n', rows[2]['target'])
        for row in rows:
            trace = row['target'].split('</think>')[0]
            self.assertNotIn('point_2d', trace)
            self.assertNotIn('[', trace)

    def test_wrong_pin_question_and_kind_fail_closed(self):
        self.assertIsNone(locate.validate_config({}))
        for value in (None, True, 'pointing-locate-v1', {**locate.RULE_PIN, 'sha256':'0'*64}):
            with self.assertRaisesRegex(ValueError, 'exact Locate rule'):
                locate.validate_config({'pointing_locate':value})
        for field, value in (('label','table'), ('label','chair\nextra'), ('frame',True), ('kind','gt_absent')):
            row = copy.deepcopy(self.rows[0]); row['pointing'][field] = value
            with self.assertRaises(ValueError): locate.render(row, '{"point_2d": [3, 4]}')
        with self.assertRaisesRegex(ValueError, 'only to pointing'):
            data.build_stream(self.source, self.division, self.root/'vqa', 'vqa', pointing_locate=locate.RULE_PIN)

    def test_prepared_store_refuses_missing_rule_and_any_wrong_target(self):
        receipt = self.build('marked', locate.RULE_PIN)
        with self.assertRaisesRegex(ValueError, 'receipt lacks'):
            locate.assert_store({k:v for k,v in receipt.items() if k!='pointing_locate'}, locate.RULE_PIN)
        row = saved(receipt)[0]
        for target in (data.READOUT_TARGET+'{"point_2d": [3, 4]}',
                       row['target'].replace('Locate the', 'Find the'),
                       row['target'].replace('frame 12.', 'frame 13.')):
            with self.assertRaises(ValueError): locate.assert_target({**row,'target':target})
        path = self.root/'corrupt.sqlite'
        with sqlite3.connect(path) as conn:
            conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
            conn.execute('INSERT INTO rows VALUES (0,?,?)', (json.dumps({**row,'target':'bad'}), '{}'))
        with self.assertRaises(ValueError):
            locate.assert_store({**receipt, 'database':file_pin(path), 'count':1}, locate.RULE_PIN)

    def test_decision_token_visible_and_null_including_merged_tokens(self):
        for absent in (False, True):
            prefix = '<think>\nLocate the lamp in frame '
            punctuation = ': it' if absent else '.\n'
            rest = ' is not visible in that frame.\n</think>\n\n{"point_2d": null}' if absent else '</think>\n\n{"point_2d": [3, 4]}'
            for merged in (False, True):
                pieces = [prefix, '12'+punctuation, rest] if merged else [prefix, '1', '2', punctuation, rest]
                labels = torch.tensor([[-100, *range(len(pieces)), -100]])
                weights = data.pointing_token_weights(labels, pieces.__getitem__, pointing_locate=locate.RULE_PIN)
                selected = 2 if merged else 4
                self.assertEqual(int(weights.argmax()), selected)
                self.assertAlmostEqual(float(weights[0, selected]/weights[0, 1]), 5.0, places=5)
                self.assertAlmostEqual(float(weights[labels != -100].mean()), 2.0, places=5)
                self.assertEqual(weights[labels == -100].tolist(), [0., 0.])

    def test_legacy_weight_and_missing_locate_are_distinct(self):
        pieces = ['<think>\n\n</think>\n\n', '{"point_2d":', ' ', 'null', '}']
        labels = torch.arange(len(pieces)).unsqueeze(0)
        old = data.pointing_token_weights(labels, pieces.__getitem__)
        self.assertEqual(int(old.argmax()), 3)
        with self.assertRaisesRegex(ValueError, 'complete pinned Locate trace'):
            data.pointing_token_weights(labels, pieces.__getitem__, pointing_locate=locate.RULE_PIN)

    def test_rows_get_carries_rule_to_shifted_training_weights(self):
        receipt = self.build('marked', locate.RULE_PIN)
        text = saved(receipt)[1]['target']
        from student_pilot.batches import training_text
        class Processor:
            tokenizer = SimpleNamespace(decode=lambda ids: chr(ids[0]), eos_token='<|im_end|>', eos_token_id=1)
            def apply_chat_template(self, messages, *, add_generation_prompt, **kwargs):
                stem = '<|im_start|>assistant\n'
                return (stem+'<think>\n' if add_generation_prompt else
                        stem+messages[-1]['content']+self.tokenizer.eos_token+'\n')
        processor = Processor()
        prompt, supervised = training_text(processor, self.rows[1]['student_input']['question'], [], text)
        self.assertTrue(prompt.endswith('<think>\n'))
        self.assertTrue(supervised.startswith('Locate the'))
        reader = run.Rows(dict(streams={'pointing':receipt}, training_mode='final',
            pointing_weights={'decision':5,'row_mean':2}, pointing_locate=locate.RULE_PIN), processor)
        labels = torch.tensor([[-100, *map(ord,supervised), -100]])
        try:
            with patch.object(data, 'encode', return_value=({'labels':labels}, None, {})):
                batch, _, _ = reader.get('pointing', 1)
            weights = batch['aux_token_weights']
            index = int(weights.argmax())
            self.assertEqual(chr(int(labels[0,index])), ':')
            self.assertEqual(index, 1+locate.decision_offset(supervised))
        finally: reader.close()

    def prepare_fixture(self, point_receipt, name):
        """Exercise real stream gates; unrelated model/source authorities are unit-test stubs."""
        code = self.root/'code.json'; model = self.root/'model.json'; pose = self.root/'pose.json'
        if not code.exists():
            write(code, {'schema':'synthetic-unit-test'})
            write(model, {'kind':'base','base_identity':'synthetic-unit-test'})
            write(pose, dict(schema='decoupled-v-preparation-v1', count=point_receipt['count'], rehearsal=True,
                database=point_receipt['database'], model=file_pin(model), inputs={'division':self.division},
                settings=dict(anchors=list(range(1,33)), temporal_grouping='fused_pairs_all_frames',
                              camera={'point_depth':{}})))
        path = self.root/(name+'_point_receipt.json'); write(path, point_receipt)
        cfg = dict(streams={'pose':file_pin(pose), 'pointing':file_pin(path)}, code=file_pin(code),
            preparation_output=str(self.root/name), trace_program_version='3.13', training_mode='mixed',
            base_identity='synthetic-unit-test', carrier_placement=data.C1_A, recipe={},
            ground_target_filter=True, pointing_locate=locate.RULE_PIN)
        with ExitStack() as stack:
            for module, attr, value in ((run,'validate',None), (run,'authenticate','synthetic-unit-test'),
                    (run.rehearsal,'enabled',True), (run.rehearsal,'fixture_manifest',True)):
                stack.enter_context(patch.object(module,attr,return_value=value))
            return run.prepare(cfg)

    def test_carrier_prepare_requires_both_target_filter_and_locate_receipt(self):
        point = self.build('marked', locate.RULE_PIN, ground_target_filter=True)
        prepared = self.prepare_fixture(point, 'prepared')
        self.assertEqual(prepared['pointing_locate'], locate.RULE_PIN)
        for key, message in (('target_filter','target-filter'), ('pointing_locate','Locate rule')):
            with self.assertRaisesRegex(ValueError, message):
                self.prepare_fixture({k:v for k,v in point.items() if k!=key}, 'missing_'+key)

    def test_config_identity_binds_rule(self):
        self.assertNotEqual(run.identity({}), run.identity({'pointing_locate':locate.RULE_PIN}))


if __name__ == '__main__': unittest.main()
