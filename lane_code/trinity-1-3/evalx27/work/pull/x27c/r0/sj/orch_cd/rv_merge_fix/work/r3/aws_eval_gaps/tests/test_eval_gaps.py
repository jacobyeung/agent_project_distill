"""Release-level checks for full corrected VSTI and both long-context cells."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from evalpath.items import load_items,sha256
from evalpath.official import build_prompt_context
from scoring import score_item,benchmark_summary
from cells import frame_count,validate_token_budget
from data import tasks_for

COUNTS={'camera_movement_direction':913,'camera_obj_abs_dist':905,'camera_obj_rel_dist_v3':856,
        'camera_displacement':833,'obj_obj_relative_pos_lr':605,'obj_obj_relative_pos_nf':556,
        'camera_obj_rel_dist_v2':493,'obj_obj_relative_pos_ud':484,'camera_obj_rel_dist_v1':91}
def pin(name):
    p=ROOT/'inputs'/name
    return dict(path=str(p),sha256=sha256(p))
def full_spec():
    return dict(benchmark='vstifull',rows=pin('vstibench_test.json'),erratum=pin('vstibench_erratum_dropped_items.json'),videos=pin('vsti_videos.json'))
def full():return load_items(full_spec(),dict(video_root='/scratch/videos'))

class FullVSTI(unittest.TestCase):
    def test_release_count_types_and_flags(self):
        rows=full()
        self.assertEqual(len(rows),5736);self.assertEqual(len({r['example_id'] for r in rows}),5736)
        self.assertEqual(Counter(r['question_type'] for r in rows),COUNTS)
        self.assertEqual(sum(r['frame_ref_m_lt_32'] for r in rows),444)
        self.assertEqual(sum(r['erratum'] for r in rows),0)
        raw={str(r['id']):r for r in json.loads((ROOT/'inputs/vstibench_test.json').read_text())}
        for r in rows:
            self.assertEqual(r['question'],raw[r['example_id']]['question'])
            self.assertEqual(r['options'],raw[r['example_id']]['options'] or [])

    def test_all_450_subset_prompts_labels_and_scores(self):
        old=load_items(dict(benchmark='vstiv3',version='v3',rows=pin('vstibench_repr_450_v3.json')),dict(video_root='/scratch/videos'))
        new={r['example_id']:r for r in full()}
        self.assertEqual(len(old),450)
        for a in old:
            b=new[a['example_id']]
            self.assertEqual(build_prompt_context(a,'ours'),build_prompt_context(b,'ours'))
            self.assertEqual(str(a['ground_truth']),str(b['ground_truth']))
            for answer in (str(a['ground_truth']),'A','B','0','1.2','nonsense',''):
                raw='<think>test</think>\n'+answer
                self.assertEqual(score_item(a,raw,8),score_item(b,raw,8))

    def test_full_pin_and_count_refuse(self):
        rows=json.loads((ROOT/'inputs/vstibench_test.json').read_text())[:-1]
        p=ROOT/'checks/short_vsti.json';p.write_text(json.dumps(rows))
        spec=full_spec();spec['rows']=dict(path=str(p),sha256=sha256(p))
        with self.assertRaisesRegex(ValueError,'5736'):load_items(spec,dict(video_root='/scratch/videos'))
        spec=full_spec();spec['rows']['sha256']='0'*64
        with self.assertRaises(ValueError):load_items(spec,dict(video_root='/scratch/videos'))

    def test_standard_frames_and_budget(self):
        c=dict(layout='spread',benchmarks=['vstifull'],frames=32)
        self.assertEqual(frame_count(c),32)
        for extra in ({'frames':64},{'layout':'paired'},{'question_frames':True},{'valid_slots':[1]},{'anchor_labels':True}):
            with self.assertRaises(ValueError):frame_count({**c,**extra})
        for n,total in [(96,30912),(128,35072)]:
            c=dict(layout='spread',benchmarks=['devrows'],frames=n,frame_set='uniform' if n==96 else 'nested')
            self.assertEqual(frame_count(c),n);self.assertEqual(validate_token_budget(c),total)
            with self.assertRaises(ValueError):validate_token_budget(c,total-1)

    def test_bootstrap_resolves_erratum_and_videos(self):
        spec=importlib.util.spec_from_file_location('bootstrap',ROOT/'kit/b/1.py')
        boot=importlib.util.module_from_spec(spec);spec.loader.exec_module(boot)
        q=dict(datasets=[dict(rows={'path':'$Q/1.json'},erratum={'path':'$Q/2.json'},videos={'path':'$Q/3.json'})])
        boot.resolve_inputs(q,ROOT/'checks')
        for pin in q['datasets'][0].values():self.assertFalse(pin['path'].startswith('$Q/'))

    def test_filtered_summary(self):
        tasks=full()[:20]
        rows=[dict(t,status='complete',**score_item(t,'</think>\n'+str(t['ground_truth']),4)) for t in tasks]
        summary=benchmark_summary(rows,tasks,True)
        self.assertEqual(summary['numbers_status'],'eligible')
        self.assertEqual(summary['overall_score'],1)
        self.assertNotIn('excluding_erratum',summary['filtered_scores'])
        for key in ('excluding_frame_ref_m_lt_32',):
            self.assertEqual(summary['filtered_scores'][key]['overall_score'],1)

if __name__=='__main__':unittest.main()
