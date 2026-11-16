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
    d = dict(CLEAN, qid=qid, type=qtype, answer=answer, gt_instances=gt, operands=list(gt), question='q?',
             options=OPTS if qtype in A.OPTION else [])
    d.update(kw)
    return d


OPTS = ['A. left', 'B. right', 'C. back', 'D. front']


def record(qid, qtype, answer, gt_answer, status=None, options=None):
    call = '<ground obj="chair">'
    resp = '<tool_response>\n' + (status or 'chair: 3 instances') + '\n</tool_response>'
    tail = ('\n</think>\n<answer>' + answer + '</answer>') if status is None else '\nI answer from the frames.\n</think>\n<answer>' + answer + '</answer>'
    options = (OPTS if qtype in A.OPTION else []) if options is None else options
    rec = dict(qid=qid, type=qtype, question='q?', options=options, answer=answer, gt_answer=gt_answer, candidate_id='c',
               spec_version='3.14', events=[dict(call=call, response=resp)],
               suffix='<think>\nI will ground the chairs.\n' + call + '\n' + resp + tail)
    if qtype in A.OPTION:
        rec['answer_content'] = dict(o.split('. ', 1) for o in options).get(answer)
    return seal(rec)


def seal(rec, pipeline_sha256='0' * 64):
    """Stand-in for replay_receipt(): the fixture has no Session, so the receipt is written directly."""
    rec['replay'] = dict(function=A.REPLAY_FUNCTION, ok=True, session_sha256=pipeline_sha256,
                         events_sha256=A.events_sha256(rec['events'], rec['spec_version']))
    return rec


def resp(qid='q1', pred='3', status='ok', sel=None, qtype='object_counting', gt_answer='3', **kw):
    r = dict(qid=qid, pred=pred, status=status, pipeline='b04_reader', pipeline_sha256='0' * 64,
             selected=copy.deepcopy(CHAIRS) if sel is None else sel,
             record=record(qid, qtype, str(pred).strip() if status == 'ok' else '3', gt_answer,
                           None if status == 'ok' else status))
    r.update(kw)
    return r


def dec(it, r, e):
    """decide() after re-sealing an edited record, to probe the checks that run after the replay receipt."""
    if r is not None and isinstance(r.get('record'), dict) and 'events' in r['record']:
        seal(r['record'], r.get('pipeline_sha256', '0' * 64))
    return A.decide(it, r, e)


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

    def test_review2_identifier_bypasses(self):
        for room, want in (('d1/scene0155_99', 'eligibility_error'), ('scannet++/09c1414f1b', 'eligibility_error'),
                           ('scannet/scene0161_99', 'eligibility_error'), ('d1/scene0183', 'eligibility_error')):
            self.assertTrue(E.reason(dict(item(), room=room)).startswith(want), room)
        self.assertEqual(E.reason(dict(item(), scene='scannet++/09c1414f1b', dataset='scannet++', room=None)), 'benchmark')
        r0 = sorted(r for r in E.r0 if r.startswith('scannet/'))[0]
        self.assertEqual(E.reason(dict(item(), dataset='d1', scene=r0.split('/')[1] + '_00', room=None)), 'r0_reserve')

    def test_review2_clean_aliases_resolve(self):
        for ds, sc, room in (('d2', 'v012679495aa0', 'scannetpp/216b9e55e8'), ('d3', 'v00475f483e27', 'arkitscenes/44796432')):
            it = dict(item(), dataset=ds, scene=sc, room=None)
            self.assertIsNone(E.reason(it), sc)
            self.assertEqual(it['room_key'], room)
        it = dict(item(), dataset='scannet++', scene='00dd871005', room=None)
        self.assertIsNone(E.reason(it))
        a = dict(item(), dataset='d3', scene='40777060', room='d3/40777060')
        b = dict(item(), dataset='arkitscenes', scene='arkitscenes/40777060', room='arkitscenes/40777060')
        ra, rb = E.reason(a), E.reason(b)
        self.assertEqual((ra, rb), (None, None))
        self.assertEqual(a['room_key'], b['room_key'])

    def test_every_identifier_is_checked(self):
        self.assertTrue(E.reason(dict(item(), room='d1/scene0155')).startswith('eligibility_error:identity_conflict'))
        self.assertTrue(E.reason(dict(item(), physical_group='scannet/scene0011_00')).startswith('eligibility_error:identity_conflict'))
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
        for bad in ('nan', 'inf', 'abc', '', '2e2', ' 200', 200.0):
            self.assertEqual(mk(bad)[0], 'direct', bad)
        self.assertEqual(mk('0', '1e-1000000000'), ('drop', 'gt_malformed'))
        self.assertEqual(mk('0', '0')[0], 'head')
        self.assertEqual(mk('0.01', '0')[0], 'direct')
        self.assertEqual(mk('1', '-1'), ('drop', 'negative_gt'))
        self.assertEqual(mk('1.15000000000000000000000000001', '1')[0], 'direct')
        self.assertEqual(mk('1.15', '1')[0], 'head')

    def test_options_and_counts_exact(self):
        g = {'a': ['a:0'], 'b': ['b:0']}
        def d(p, a):
            return A.decide(item(qtype='object_rel_direction_hard', answer=a, gt=g),
                            resp(pred=p, sel=g, qtype='object_rel_direction_hard', gt_answer=a), E)[0]
        self.assertEqual(d('B', 'B'), 'head')
        for bad in ('C', 'Banana', 'B but actually C', 'b', 'B.', None, ' B'):
            self.assertEqual(d(bad, 'B'), 'direct', bad)
        self.assertEqual(d(None, None), 'drop')
        self.assertEqual(d('B', ' B'), 'drop')
        for bad in ('3.0', '3.0000000000000001', '03', ' 3x', ' 3', 3):
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
        self.assertEqual(dec(item(), resp(pipeline=''), E), ('drop', 'response_without_provenance'))
        self.assertEqual(dec(item(), resp(pipeline_sha256='not-a-sha256'), E), ('drop', 'response_without_provenance'))
        r = resp()
        del r['record']
        self.assertEqual(dec(item(), r, E), ('drop', 'record_missing'))
        r = resp()
        r['record']['answer'] = '4'
        self.assertEqual(dec(item(), r, E)[0], 'drop')
        r = resp(pred='4')
        r['record'] = record('q1', 'object_counting', '3', '3')
        self.assertEqual(dec(item(answer='4'), r, E), ('drop', 'record_gt'))
        r = resp()
        r['pred'] = '3'
        r['record'] = dict(record('q1', 'object_counting', '3', '3'))
        r['record']['answer'] = '3'
        r2 = dict(r, pred=' 3')
        self.assertEqual(dec(item(), r2, E), ('direct', 'response_wrong'))
        r = resp()
        r['record']['suffix'] = r['record']['suffix'].replace('<answer>3</answer>', '<answer>4</answer>')
        self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'))
        r = resp()
        r['record']['events'][0]['response'] = 'other'
        self.assertEqual(dec(item(), r, E)[0], 'drop')
        r = resp()
        r['record']['gt_answer'] = '4'
        self.assertEqual(dec(item(), r, E), ('drop', 'record_gt'))
        r = resp()
        r['record']['gt_answer'] = ' 3 '
        self.assertEqual(dec(item(), r, E), ('drop', 'record_gt'))
        for flag, value in (('gt_agrees', False), ('training_admitted', True), ('not_seen', True)):
            r = resp()
            r['record'][flag] = value
            self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'), flag)
        r = resp()
        r['record']['suffix'] = r['record']['suffix'][len('<think>\n'):]
        self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'))
        r = resp()
        r['record']['suffix'] = r['record']['suffix'].replace('<ground obj="chair">', 'not a call')
        r['record']['events'][0]['call'] = 'not a call'
        self.assertEqual(dec(item(), r, E), ('drop', 'record_call_grammar'))
        r = resp()
        old = r['record']['events'][0]['response']
        r['record']['suffix'] = r['record']['suffix'].replace(old, 'garbage')
        r['record']['events'][0]['response'] = 'garbage'
        self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'))
        r = resp()
        r['record']['spec_version'] = '9.99'
        self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'))

    def test_review3_gt_whitespace_and_options(self):
        r = resp(pred='3')
        r['record'] = record('q1', 'object_counting', '3', ' 3 ')
        self.assertEqual(A.decide(item(answer=' 3 '), r, E)[0], 'drop')
        g = {'a': ['a:0'], 'b': ['b:0']}
        it = item(qtype='object_rel_distance', answer='B', gt=g)
        ok = resp(pred='B', sel=g, qtype='object_rel_distance', gt_answer='B')
        self.assertEqual(A.decide(it, ok, E)[0], 'head')
        r = copy.deepcopy(ok)
        del r['record']['answer_content']
        self.assertEqual(A.decide(it, r, E), ('drop', 'record_options'))
        r = copy.deepcopy(ok)
        r['record']['options'] = ['A. right', 'B. left', 'C. back', 'D. front']
        r['record']['answer_content'] = 'left'
        self.assertEqual(A.decide(it, r, E), ('drop', 'record_question'))
        r = copy.deepcopy(ok)
        r['record']['answer_content'] = 'left'
        self.assertEqual(A.decide(it, r, E)[0], 'drop')
        r = copy.deepcopy(ok)
        r['record']['question'] = 'other?'
        self.assertEqual(A.decide(it, r, E), ('drop', 'record_question'))

    def test_review3_recovery(self):
        r = resp(status='chair: not seen', pred=None)
        r['record']['not_seen'] = True
        self.assertEqual(dec(item(), r, E), ('recovery', 'real_failure'))
        r = resp(status='chair: not seen', pred=None)
        r['record']['events'][0]['call'] = '<ground obj="table">'
        r['record']['suffix'] = r['record']['suffix'].replace('<ground obj="chair">', '<ground obj="table">')
        self.assertEqual(dec(item(), r, E), ('drop', 'record_status_operand'))
        g = {'sofa': ['sofa:0']}
        r = resp(status='chair: not seen', pred=None, qtype='object_abs_distance', gt_answer='-1')
        self.assertEqual(dec(item(qtype='object_abs_distance', answer='-1', gt=g), r, E), ('drop', 'negative_gt'))

    def test_review5(self):
        r = resp(qtype='object_rel_direction_medium', pred='A', gt_answer='A', sel={'a': ['a:0']})
        call = '<angle S=P1 F=P2 Q=P3 rule=medium>'
        body = '<tool_response>\ntheta 45 deg; left\n</tool_response>'
        rec = r['record']
        rec['events'].append(dict(call=call, response=body))
        rec['suffix'] = rec['suffix'].replace('\n</think>', '\n' + call + '\n' + body + '\n</think>')
        seal(rec)
        it = item(qtype='object_rel_direction_medium', answer='A', gt={'a': ['a:0']})
        self.assertEqual(A.decide(it, r, E)[1], 'sealed_pack_refused:unprinted_point_reference')
        self.assertTrue(A.call_ok(call, A.call_patterns()))
        self.assertFalse(A.call_ok('<ground obj=" chair">', A.call_patterns()))
        r = resp()
        r['record']['events'][0]['call'] = '<ground obj=" chair">'
        r['record']['suffix'] = r['record']['suffix'].replace('<ground obj="chair">', '<ground obj=" chair">')
        seal(r['record'])
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_call_grammar'))
        r = resp()
        del r['record']['replay']
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_replay_missing'))
        r = resp()
        r['record']['replay']['session_sha256'] = '1' * 64
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_replay_missing'))
        r = resp()
        r['record']['events'][0]['response'] += ' '
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_replay_missing'))
        r = resp(status='chair: not seen', pred=None)
        pre = dict(call='<ground obj="table">', response='<tool_response>\nmask_source_unavailable_for_type\n</tool_response>')
        r['record']['events'].insert(0, pre)
        r['record']['suffix'] = r['record']['suffix'].replace('<think>\n', '<think>\n' + pre['call'] + '\n' + pre['response'] + '\n', 1)
        seal(r['record'])
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_operator_fault'))
        for body in ('chair: unresolved', 'chair: box unavailable', 'frame unavailable', 'chair: 0 found'):
            r = resp()
            old = r['record']['events'][0]['response']
            new = '<tool_response>\n' + body + '\n</tool_response>'
            r['record']['events'][0]['response'] = new
            r['record']['suffix'] = r['record']['suffix'].replace(old, new)
            seal(r['record'])
            self.assertEqual(A.decide(item(), r, E), ('drop', 'record_failure_in_head'), body)
        for state in ('unresolved', 'box unavailable'):
            self.assertEqual(A.decide(item(), resp(status='chair: ' + state, pred=None), E), ('recovery', 'real_failure'), state)

    def test_replay_receipt_uses_sealed_replay(self):
        rec = record('q1', 'object_counting', '3', '3')
        del rec['replay']

        class Stub:
            spec_version = '3.14'

            def __init__(self, bodies):
                self.bodies = list(bodies)

            def execute(self, call):
                return self.bodies.pop(0)
        receipt = A.replay_receipt(rec, Stub(['chair: 3 instances']), '0' * 64)
        self.assertEqual(receipt['events_sha256'], A.events_sha256(rec['events'], '3.14'))
        old = Stub(['chair: 3 instances'])
        old.spec_version = '3.12.2'
        with self.assertRaises(ValueError):
            A.replay_receipt(rec, old, '0' * 64)

        class Legacy:  # the ground_v312 Session defines no spec_version
            def execute(self, call):
                return 'chair: 3 instances'
        legacy = dict(rec, spec_version='3.12.2')
        self.assertEqual(A.replay_receipt(legacy, Legacy(), '0' * 64)['events_sha256'], A.events_sha256(rec['events'], '3.12.2'))
        with self.assertRaises(ValueError):
            A.replay_receipt(rec, Legacy(), '0' * 64)
        with self.assertRaises(Exception):
            A.replay_receipt(rec, Stub(['chair: 4 instances']), '0' * 64)

    def test_review6(self):
        r = resp()
        r['record']['suffix'] = r['record']['suffix'].replace('<think>\n', '<think>\n<ground obj="table">\n', 1)
        self.assertEqual(dec(item(), r, E), ('drop', 'record_unrecorded_tag'))
        r = resp(status='chair: not seen', pred=None)
        r['record']['suffix'] = r['record']['suffix'].replace('<think>\n', '<think>\n<gap a="x" b="y">\n', 1)
        self.assertEqual(dec(item(), r, E), ('drop', 'record_unrecorded_tag'))
        self.assertEqual(A.decide(item(), resp(sel={'chair': {'chair:1': False, 'chair:2': 0, 'chair:3': 0}}), E),
                         ('direct', 'mask_mismatch:chair'))
        self.assertEqual(A.decide(item(answer='3', gt={'chair': 'abc'}), resp(sel={'chair': 'abc'}), E),
                         ('direct', 'mask_unverified'))

    def test_review7(self):
        r = resp()
        r['record']['suffix'] = r['record']['suffix'].replace('<think>\n', '<think>\nOn the floor, cross > 0 means left; cross < 0 means right.\n', 1)
        self.assertEqual(dec(item(), r, E), ('head', 'right_and_masks_match'))
        r = resp()
        r['record']['spec_version'] = '3.13'
        self.assertEqual(A.decide(item(), r, E), ('drop', 'record_replay_missing'))

    def test_review4(self):
        for call in ('<ground obj="chair"', '<ground obj="chair" junk>', '<fly obj="chair">'):
            for status in ('ok', 'chair: not seen'):
                r = resp(status=status, pred='3' if status == 'ok' else None)
                old = r['record']['events'][0]['call']
                r['record']['events'][0]['call'] = call
                r['record']['suffix'] = r['record']['suffix'].replace(old, call)
                self.assertEqual(dec(item(), r, E), ('drop', 'record_call_grammar'), (call, status))
        for body in ('chair: not seen', 'mask_source_unavailable_for_type'):
            r = resp()
            old = r['record']['events'][0]['response']
            new = '<tool_response>\n' + body + '\n</tool_response>'
            r['record']['events'][0]['response'] = new
            r['record']['suffix'] = r['record']['suffix'].replace(old, new)
            self.assertIn(dec(item(), r, E), (('drop', 'record_failure_in_head'), ('drop', 'record_operator_fault')), body)
        g = {'a': ['a:0']}
        r = resp(status='chair: not seen', pred=None, qtype='object_rel_distance', gt_answer='Z')
        self.assertEqual(dec(item(qtype='object_rel_distance', answer='Z', gt=g), r, E), ('drop', 'gt_not_an_option'))
        r = resp(pred='1', sel={'chair': [None]}, gt_answer='1')
        self.assertEqual(dec(item(answer='1', gt={'chair': [None]}), r, E), ('direct', 'mask_unverified'))
        r = resp(pred='1', sel={'chair': [None]}, gt_answer='1')
        self.assertEqual(dec(item(answer='1', gt={'chair': ['chair:1']}), r, E)[0], 'direct')
        name = 'chair: office'
        r = resp(status=name + ': not seen', pred=None)
        call = '<ground obj="' + name + '">'
        r['record']['suffix'] = r['record']['suffix'].replace('<ground obj="chair">', call)
        r['record']['events'][0]['call'] = call
        self.assertEqual(dec(item(gt={name: ['c:1']}), r, E), ('recovery', 'real_failure'))

    def test_recovery_needs_the_failure_event(self):
        self.assertEqual(dec(item(), resp(status='chair: not seen', pred=None), E), ('recovery', 'real_failure'))
        r = resp(status='chair: not seen', pred=None)
        ok = record('q1', 'object_counting', '3', '3')
        r['record']['events'] = ok['events']
        r['record']['suffix'] = ok['suffix'].replace('\n</think>', '\nchair: not seen\n</think>')
        self.assertEqual(dec(item(), r, E), ('drop', 'record_status'))
        r = resp(status='chair: not seen', pred=None)
        r['record']['suffix'] = r['record']['suffix'].rsplit('\n</think>', 1)[0]
        self.assertTrue(dec(item(), r, E)[1].startswith('sealed_pack_refused'))

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
