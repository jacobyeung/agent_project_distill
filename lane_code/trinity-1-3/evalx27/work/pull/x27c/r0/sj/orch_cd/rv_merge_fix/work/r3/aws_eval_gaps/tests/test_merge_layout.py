"""CPU regression tests for explicit cell layouts and pinned ReVSI frames."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evaluator'))
import merge as merger
from cells import frame_count
from evalpath.items import digest
from media import frame_list
from scoring import score_item
from worker import read_journal


def fixture(benchmark='revsi', layout='duplicate', frames=32):
    task=dict(benchmark=benchmark, example_id='1', question_type='object_counting_single' if benchmark=='revsi' else 'object_counting',
              ground_truth='3', options=[], question='How many?', source_frame_indices=[59*i for i in range(frames)])
    raw='reason\n</think>\n3'
    row=dict(task,key=benchmark+':1',layout=layout,frames=frames,status='complete',raw_generation=raw,finish_reason='stop',
             media={'metadata':{'frames_indices':[i for i in task['source_frame_indices'] for _ in range(2 if layout=='duplicate' else 1)]}},
             at_4096={},**score_item(task,raw,5))
    return task,row


@unittest.skipUnless(hasattr(merger,'check_row'),'This kit has no pinned ReVSI check_row')
class PinnedFrames(unittest.TestCase):
    def setUp(self):
        self.task,self.row=fixture()

    def check(self,row=None,task=None,layout='duplicate',frames=32):
        merger.check_row(self.row if row is None else row,self.task if task is None else task,frames,layout)

    def test_correct_duplicate_and_no_mutation(self):
        before=deepcopy(self.row);self.check();self.assertEqual(self.row,before)

    def test_duplicate_cell_spread_row(self):
        self.row['layout']='spread'
        with self.assertRaisesRegex(ValueError,'layout'):self.check()

    def test_spread_cell_duplicate_row(self):
        with self.assertRaisesRegex(ValueError,'layout'):self.check(layout='spread')

    def test_wrong_repeat_counts(self):
        for repeat in (0,1,3,4):
            with self.subTest(repeat=repeat):
                self.row['media']['metadata']['frames_indices']=[i for i in self.task['source_frame_indices'] for _ in range(repeat)]
                with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check()

    def test_swapped_anchor_pairs(self):
        indices=self.row['media']['metadata']['frames_indices'];indices[2:6]=indices[4:6]+indices[2:4]
        with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check()

    def test_swapped_individual_indices(self):
        indices=self.row['media']['metadata']['frames_indices'];indices[1],indices[2]=indices[2],indices[1]
        with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check()

    def test_contains_all_pins_but_wrong_order(self):
        self.row['media']['metadata']['frames_indices']=self.task['source_frame_indices']*2
        with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check()

    def test_extra_missing_or_substituted_index(self):
        original=deepcopy(self.row)
        for indices in (original['media']['metadata']['frames_indices']+[0],original['media']['metadata']['frames_indices'][:-1],
                        [9999]+original['media']['metadata']['frames_indices'][1:]):
            with self.subTest(indices=indices[:3]):
                self.row['media']['metadata']['frames_indices']=indices
                with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check()

    def test_missing_layout(self):
        self.row.pop('layout')
        with self.assertRaisesRegex(ValueError,'layout'):self.check()

    def test_error_row_missing_or_wrong_layout(self):
        self.row['status']='error'
        for layout in (None,'spread'):
            self.row['layout']=layout
            with self.assertRaisesRegex(ValueError,'layout'):self.check()

    def test_spread_32_and_64_unchanged(self):
        for frames in (32,64):
            task,row=fixture(layout='spread',frames=frames)
            self.check(row,task,'spread',frames)
            row['media']['metadata']['frames_indices']*=2
            with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check(row,task,'spread',frames)

    def test_other_layout_keeps_exact_equality(self):
        task,row=fixture(layout='P0.5');self.check(row,task,'P0.5')
        row['media']['metadata']['frames_indices']*=2
        with self.assertRaisesRegex(ValueError,'ReVSI frames'):self.check(row,task,'P0.5')

    def test_non_revsi_does_not_gain_pinned_index_check(self):
        for benchmark in ('vsi500','devrows','vstifull'):
            for layout in ('spread','duplicate'):
                task,row=fixture(benchmark,layout);row['media']['metadata']['frames_indices']=[999]
                self.check(row,task,layout)

    def test_identity_pin_and_rescore_checks_remain(self):
        for key,value in (('example_id','wrong'),('frames',64),('ground_truth','4'),('score',0.),('response_text','wrong')):
            with self.subTest(key=key):
                row={**self.row,key:value}
                with self.assertRaises(ValueError):self.check(row)

    def test_error_rows_still_skip_media_and_scoring(self):
        row={**self.row,'status':'error'};row.pop('media');row.pop('raw_generation');self.check(row)


class LayoutPaths(unittest.TestCase):
    def merge_case(self,layout='duplicate',row_layout='duplicate',benchmark='vsi500'):
        task,row=fixture(benchmark,layout)
        if row_layout is None:row.pop('layout')
        else:row['layout']=row_layout
        out=Path(tempfile.mkdtemp());d=out/'0';d.mkdir()
        cfg=dict(cells=[dict(model='test',layout=layout,benchmarks=[benchmark])],datasets=[dict(benchmark=benchmark)],roots={},binding='test',gpus=1,output=str(out))
        row['binding']=digest({'request':'test','cell':0})
        (d/'g0.jsonl').write_text(json.dumps(row)+'\n')
        with patch.object(merger,'tasks_for',return_value=[task]):result=merger.merge(cfg,0,'test')
        return result,row,json.loads((d/'items_test.jsonl').read_text())

    def test_merge_accepts_matching_layouts(self):
        for layout in ('spread','duplicate'):
            result,row,item=self.merge_case(layout,layout)
            self.assertEqual(result['benchmarks']['vsi500']['completed'],1)
            self.assertEqual(item['media'],row['media']);self.assertEqual(item['layout'],layout)

    def test_merge_refuses_crossed_and_missing_layout(self):
        for layout,record in (('duplicate','spread'),('spread','duplicate'),('duplicate',None),('spread',None)):
            with self.subTest(layout=layout,record=record):
                with self.assertRaisesRegex(ValueError,'layout'):self.merge_case(layout,record)

    @unittest.skipUnless(hasattr(merger,'check_row'),'No pinned ReVSI admission in this kit')
    def test_duplicate_revsi_end_to_end(self):
        result,row,item=self.merge_case(benchmark='revsi')
        self.assertEqual(result['benchmarks']['revsi']['completed'],1)
        self.assertEqual(item['media'],row['media'])

    def test_resume_accepts_valid_and_ignores_partial(self):
        p=Path(tempfile.mkdtemp())/'g.jsonl'
        p.write_text(json.dumps(dict(key='a',binding='b',layout='duplicate',status='complete'))+'\n{"partial":')
        self.assertEqual(set(read_journal(p,'b','duplicate')),{'a'})
        with self.assertRaisesRegex(ValueError,'binding'):read_journal(p,'wrong','duplicate')

    def test_resume_refuses_missing_or_different_layout_before_skip(self):
        for status in ('complete','error'):
            for layout in (None,'spread'):
                with self.subTest(status=status,layout=layout):
                    p=Path(tempfile.mkdtemp())/'g.jsonl';r=dict(key='a',binding='b',status=status)
                    if layout is not None:r['layout']=layout
                    p.write_text(json.dumps(r)+'\n')
                    with self.assertRaisesRegex(ValueError,'layout'):read_journal(p,'b','duplicate')

    def test_declared_duplicate_means_two_in_media(self):
        anchors=[i*59 for i in range(32)]
        indices,fallback=frame_list(anchors,10,2000,'duplicate')
        self.assertEqual(indices,[i for i in anchors for _ in range(2)]);self.assertEqual(fallback,[])
        self.assertEqual(frame_count(dict(layout='duplicate',benchmarks=['vsi500'])),32)

if __name__=='__main__':unittest.main(verbosity=2)
