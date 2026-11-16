import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import assign as A

E = A.Eligibility()
CLEAN = dict(dataset='scannet', scene='scannet/scene0232_02', room='d1/scene0232')
CHAIRS = {'chair': ['chair:1', 'chair:2', 'chair:3']}


def item(qid='q1', qtype='object_counting', answer='3', gt=None, **kw):
    gt = CHAIRS if gt is None else gt
    d = dict(CLEAN, qid=qid, type=qtype, answer=answer, gt_instances=gt, operands=list(gt))
    d.update(kw)
    return d


def record(qid, qtype, answer, gt_answer, status=None):
    call = '<ground obj="chair">'
    resp = '<tool_response>\n' + (status or 'chair: 3 instances') + '\n</tool_response>'
    tail = ('\n</think>\n<answer>' + answer + '</answer>') if status is None else '\nI answer from the frames.\n</think>\n<answer>' + answer + '</answer>'
    return dict(qid=qid, type=qtype, question='q?', options=[], answer=answer, gt_answer=gt_answer, candidate_id='c',
                spec_version='3.14', events=[dict(call=call, response=resp)],
                suffix='<think>\nI will ground the chairs.\n' + call + '\n' + resp + tail)


def resp(qid='q1', pred='3', status='ok', sel=None, qtype='object_counting', gt_answer='3', **kw):
    r = dict(qid=qid, pred=pred, status=status, pipeline='b04_reader', pipeline_sha256='0' * 64,
             selected=copy.deepcopy(CHAIRS) if sel is None else sel,
             record=record(qid, qtype, str(pred).strip() if status == 'ok' else '3', gt_answer,
                           None if status == 'ok' else status))
    r.update(kw)
    return r


class Eligibility(unittest.TestCase):
    def test_clean_scene_is_eligible(self):
        it = item()
        self.assertIsNone(E.reason(it))
        self.assertEqual(it['room_key'], 'scannet/scene0232')

    def test_alias_resolves_to_same_room(self):
        it = dict(item(), dataset='d1', scene='vb330148be642', room=None)
        self.assertIsNone(E.reason(it))
        self.assertEqual(it['room_key'], 'scannet/scene0232')

    def test_refuses_dev_benchmark_withheld_r0(self):
        self.assertEqual(E.reason(dict(item(), dataset='arkitscenes', scene='arkitscenes/41069053', room=None)), 'dev_s1')
        self.assertEqual(E.reason(dict(item(), scene='scannet/scene0011_00', room=None)), 'benchmark')
        withheld = json.loads((A.AUTH / 'WITHHELD_ROOMS_80.json').read_text())
        for room, aliases in withheld['aliases'].items():
            for alias in aliases:
                ds, sc = alias.split('/', 1)
                self.assertIsNotNone(E.reason(dict(dataset=ds, scene=sc, room=room)), alias)
        r0 = sorted(r for r in E.r0 if r.startswith('scannet/'))[0]
        self.assertEqual(E.reason(dict(item(), scene=r0 + '_00', room=None)), 'r0_reserve')

    def test_every_identifier_is_checked(self):
        self.assertEqual(E.reason(dict(item(), room='d1/scene0155')), 'dev_s1')
        self.assertEqual(E.reason(dict(item(), physical_group='scannet/scene0011_00')), 'benchmark')
        self.assertTrue(E.reason(dict(item(), dataset='scannet', scene='arkitscenes/41069053')).startswith('eligibility_error'))
        self.assertTrue(E.reason(dict(item(), dataset='nope')).startswith('eligibility_error'))
        self.assertTrue(E.reason(dict(item(), dataset='d1', scene='vunknown000000', room=None)).startswith('eligibility_error'))


class Decide(unittest.TestCase):
    def test_head_only_when_right_and_masks_match(self):
        self.assertEqual(A.decide(item(), resp(), E), ('head', 'right_and_masks_match'))
        self.assertEqual(A.decide(item(), resp(pred='4'), E)[0], 'direct')
        self.assertEqual(A.decide(item(), resp(sel={'chair': ['chair:1', 'chair:2', 'chair:9']}), E), ('direct', 'mask_mismatch:chair'))
        self.assertEqual(A.decide(item(), resp(sel={'chair': ['chair:1', 'chair:2', 'chair:3', 'chair:3']}), E)[0], 'direct')
        self.assertEqual(A.decide(item(), resp(sel={'chair': ['chair:1', 'chair:2', 'unmatched']}), E)[0], 'direct')
        self.assertEqual(A.decide(item(gt={}), resp(), E), ('direct', 'mask_unverified'))
        extra = {'chair': ['chair:1', 'chair:2', 'chair:3'], 'desk': ['desk:0']}
        self.assertEqual(A.decide(item(), resp(sel=extra), E), ('direct', 'mask_operands_differ'))

    def test_every_operand_needs_gt(self):
        g = {'chair': ['chair:3']}
        it = item(qtype='object_rel_direction_hard', answer='B', gt=g, operands=['chair', 'table'])
        self.assertEqual(A.decide(it, resp(pred='B', sel=g, qtype='object_rel_direction_hard', gt_answer='B'), E),
                         ('direct', 'mask_unverified'))

    def test_numeric_tolerance(self):
        g = {'sofa': ['sofa:0']}
        def mk(p, a='200'):
            return A.decide(item(qtype='object_abs_distance', answer=a, gt=g),
                            resp(pred=p, sel=g, qtype='object_abs_distance', gt_answer=a), E)
        self.assertEqual(mk('230')[0], 'head')
        self.assertEqual(mk('170')[0], 'head')
        self.assertEqual(mk('0.85', '1')[0], 'head')
        self.assertEqual(mk('230.01')[0], 'direct')
        for bad in ('nan', 'inf', 'abc', ''):
            self.assertEqual(mk(bad)[0], 'direct', bad)
        self.assertEqual(mk('0', '0'), ('drop', 'nonpositive_gt'))

    def test_options_and_counts_exact(self):
        g = {'a': ['a:0'], 'b': ['b:0']}
        def d(p, a):
            return A.decide(item(qtype='object_rel_direction_hard', answer=a, gt=g),
                            resp(pred=p, sel=g, qtype='object_rel_direction_hard', gt_answer=a), E)[0]
        self.assertEqual(d('B', 'B'), 'head')
        for bad in ('C', 'Banana', 'B but actually C', 'b', 'B.', None):
            self.assertEqual(d(bad, 'B'), 'direct', bad)
        self.assertEqual(d(None, None), 'direct')
        for bad in ('3.0', '3.0000000000000001', '03', ' 3x'):
            self.assertEqual(A.decide(item(), resp(pred=bad), E)[0], 'direct', bad)
        self.assertEqual(A.decide(item(answer='9007199254740992'), resp(pred='9007199254740993'), E)[0], 'direct')

    def test_statuses(self):
        self.assertEqual(A.decide(item(), resp(status='chair: not seen', pred=None), E), ('recovery', 'real_failure'))
        for bad in ('no answer required; success', 'chair: not seen yesterday; ok now', '', 'weird'):
            self.assertEqual(A.decide(item(), resp(status=bad), E), ('drop', 'unknown_status'), bad)
        self.assertEqual(A.decide(item(), resp(status='form_requires_v3.13'), E), ('drop', 'operator_fault'))
        r = resp()
        del r['status']
        self.assertEqual(A.decide(item(), r, E), ('drop', 'no_status'))

    def test_provenance_and_record(self):
        self.assertEqual(A.decide(item(), resp(pipeline=''), E), ('drop', 'response_without_provenance'))
        self.assertEqual(A.decide(item(), resp(pipeline_sha256='not-a-sha256'), E), ('drop', 'response_without_provenance'))
        r = resp()
        del r['record']
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_missing'))
        r = resp()
        r['record']['answer'] = '4'
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_answer'))
        r = resp()
        r['record']['suffix'] = r['record']['suffix'].replace('<answer>3</answer>', '<answer>4</answer>')
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_suffix'))
        r = resp()
        r['record']['events'][0]['response'] = 'other'
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_events'))
        r = resp()
        r['record']['gt_answer'] = '4'
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_gt'))

    def test_types(self):
        g = {'sofa': ['sofa:0']}
        self.assertEqual(A.decide(item(qtype='object_size_estimation', answer='200', gt=g), resp(pred='200', sel=g), E),
                         ('drop', 'no_head_grammar'))
        self.assertEqual(A.decide(item(qtype='object_rel_direction_easy', answer='A', gt=g), resp(pred='A', sel=g), E),
                         ('drop', 'no_head_grammar'))
        self.assertEqual(A.decide(item(qtype='room_size_estimation'), resp(), E), ('drop', 'type_outside_mix'))
        self.assertEqual(A.decide(item(qtype='obj_appearance_order'), resp(), E), ('drop', 'type_outside_mix'))
        self.assertEqual(A.decide(item(), None, E), ('drop', 'no_response'))
        self.assertEqual(A.decide(item(), resp(qid='q2'), E), ('drop', 'no_response'))


class Select(unittest.TestCase):
    def test_select_minority_caps_and_room_limit(self):
        ds = []
        for i in range(30):
            ds.append(dict(qid=f'h{i}', type='object_counting', room_key=f'r{i % 3}', decision='head'))
            ds.append(dict(qid=f'd{i}', type='object_counting', room_key=f'r{i % 3}', decision='direct'))
            ds.append(dict(qid=f'a{i}', type='object_abs_distance', room_key='r0', decision='direct'))
            ds.append(dict(qid=f'b{i}', type='object_abs_distance', room_key='r0', decision='head'))
            ds.append(dict(qid=f'f{i}', type='object_abs_distance', room_key=f'r{i}', decision='recovery'))
        chosen, used = A.select(ds, cap=5, per_room=4, recovery_cap=2)
        self.assertEqual(used[('object_counting', 'head')], 5)
        self.assertNotIn(('object_counting', 'direct'), used)
        self.assertEqual(used[('object_abs_distance', 'direct')], 4)
        self.assertNotIn(('object_abs_distance', 'head'), used)
        self.assertEqual(used[('object_abs_distance', 'recovery')], 2)
        again, _ = A.select(list(reversed(ds)), cap=5, per_room=4, recovery_cap=2)
        self.assertEqual([d['qid'] for d in chosen], [d['qid'] for d in again])
        for bad in (dict(cap=2001), dict(per_room=5), dict(recovery_cap=2001), dict(cap=0)):
            with self.assertRaises(ValueError):
                A.select(ds, **bad)

    def test_room_aliases_share_one_cap(self):
        its = [dict(item(qid=f'x{i}'), room=None) for i in range(4)]
        its += [dict(item(qid=f'y{i}'), dataset='d1', scene='vb330148be642', room=None) for i in range(4)]
        ds = []
        for it in its:
            decision, _ = A.decide(it, resp(qid=it['qid']), E)
            ds.append(dict(qid=it['qid'], type=it['type'], room_key=it['room_key'], decision=decision))
        chosen, used = A.select(ds)
        self.assertEqual(used[('object_counting', 'head')], 4)


class Run(unittest.TestCase):
    def test_run_end_to_end(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            items = [item(qid=f'q{i}') for i in range(3)] + [dict(item(qid='qdev'), dataset='arkitscenes', scene='arkitscenes/41069053', room=None)]
            rs = [resp(qid='q0'), resp(qid='q1', pred='5'), resp(qid='q2', status='chair: not seen'), resp(qid='qdev')]
            (t / 'i.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in items))
            (t / 'r.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rs))
            s = A.run(t / 'i.jsonl', t / 'r.jsonl', t / 'o')
            self.assertEqual(s['tally']['object_counting'], {'head:right_and_masks_match': 1, 'direct:response_wrong': 1,
                                                             'recovery:real_failure': 1, 'drop:dev_s1': 1})
            self.assertEqual(s['selected'], {'object_counting|head': 1, 'object_counting|recovery': 1})
            (t / 'r2.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rs + rs[:1]))
            with self.assertRaises(ValueError):
                A.run(t / 'i.jsonl', t / 'r2.jsonl', t / 'o2')


if __name__ == '__main__':
    unittest.main()
