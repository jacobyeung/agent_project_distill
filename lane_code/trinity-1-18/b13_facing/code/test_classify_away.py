"""Unit tests for classify_away.py on hand-written traces, plus the step-544 agreement check."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify_away as C  # noqa: E402

LANE = os.path.dirname(HERE)
M544 = os.path.join(LANE, 'work/in/t13/evalx27/work/pull/x27/res/e193/merged')
READK = os.path.join(LANE, 'work/in/t13/cont_ops/work/d0/readk')

OPTS = {'easy': ['A. right', 'B. left'], 'medium': ['A. back', 'B. left', 'C. right'],
        'hard': ['A. back-left', 'B. front-right', 'C. back-right', 'D. front-left']}
Q = {'easy': 'If I am standing by the bed and facing away from the door, is the bag to my left or to my right?',
     'medium': 'If I am standing by the bed and facing away from the door, is the bag to my left, right, or back?\n'
               'An object is to my back if I would have to turn at least 135 degrees in order to face it.',
     'hard': 'If I am standing by the bed and facing away from the door, is the bag to my front-left, front-right, '
             'back-left, or back-right?'}
HALF = ('The question has me face away from the door. That is a half turn: what was ahead is now behind me, '
        'what was behind is now ahead, and left and right swap.')
SEEN = 'Seen: bed in frame 1; door in frame 2; bag in frame 3.'


def letter(level, content):
    for o in OPTS[level]:
        if o.split('. ')[1] == content:
            return o[0]
    raise KeyError(content)


def row(level, theta, pred_content, trace, gt_content, rid='x1', question=None):
    return dict(id=rid, question=question or Q[level], options=OPTS[level], ground_truth=letter(level, gt_content),
                question_type='object_rel_direction_' + level,
                raw_generation=(trace + '\n</think>\n\n' + (letter(level, pred_content) if pred_content else '')),
                extracted_answer=letter(level, pred_content) if pred_content else None,
                label_provenance=dict(backdir=dict(forward_program_audit=dict(unrounded_theta_deg=theta))))


def twin(level, pred_content, gt_content, rid='x1'):
    return dict(id='fw_' + rid, question=Q[level].replace('facing away from', 'facing'), options=OPTS[level],
                ground_truth=letter(level, gt_content), question_type='object_rel_direction_' + level,
                raw_generation='So.\n</think>\n\n' + letter(level, pred_content),
                extracted_answer=letter(level, pred_content), label_provenance=dict(paired_away_qid=rid))


def d0(fwd_words, concl_words, clause=HALF):
    lines = [SEEN, 'If I stood at the bed facing the door, the bag would be %s.' % fwd_words]
    if clause:
        lines.append(clause)
    lines.append('So I find the bag %s.' % concl_words)
    return '\n'.join(lines)


class TestClasses(unittest.TestCase):
    def test_e_correct_d0_form(self):
        r = C.classify(row('hard', 40, 'back-right', d0('in front of me, on my left', 'at my back-right'), 'back-right'),
                       twin('hard', 'front-left', 'front-left'))
        self.assertEqual((r['cls'], r['clause']), ('e', 'turn'))
        self.assertEqual(r['transition'], 'hard:front-left->back-right')

    def test_a_toward_clause_on_away_item(self):
        t = '\n'.join([SEEN, 'Standing at the bed facing the door, I find the bag to my left.',
                       'The question has me face the door, so no turn applies.', 'So I find the bag to my left.'])
        r = C.classify(row('easy', 70, 'left', t, 'right'), twin('easy', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('a', 'toward_clause'))

    def test_a_no_clause(self):
        t = '\n'.join([SEEN, 'Standing at the bed facing the door, I find the bag to my left.', 'So I find the bag to my left.'])
        r = C.classify(row('easy', 70, 'left', t, 'right'), twin('easy', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('a', 'none'))

    def test_a_empty_trace(self):
        r = C.classify(row('easy', 70, 'left', '', 'right'), twin('easy', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('a', 'empty_trace'))

    def test_b_clause_written_not_turned(self):
        r = C.classify(row('easy', 70, 'left', d0('to my left', 'to my left'), 'right'), twin('easy', 'left', 'left'))
        self.assertEqual(r['cls'], 'b')

    def test_b_mention_only_sealed_form(self):
        t = ('Step 1: locate the centres of the bed, the door and the bag.\nStep 2: standing at the bed and facing away '
             'from the door, the bag lies 41 degrees left of straight ahead, in front.\nSo the bag is at my front-left.')
        r = C.classify(row('hard', 40, 'front-left', t, 'back-right'), twin('hard', 'front-left', 'front-left'))
        self.assertEqual((r['cls'], r['clause']), ('b', 'mention'))

    def test_c_hard_left_right_only(self):
        t = ('Step 2: standing at the bed and facing away from the door, the bag lies 41 degrees right of straight '
             'ahead, in front.\nSo the bag is at my front-right.')
        r = C.classify(row('hard', 40, 'front-right', t, 'back-right'), twin('hard', 'front-left', 'front-left'))
        self.assertEqual(r['cls'], 'c')

    def test_c_hard_front_back_only(self):
        r = C.classify(row('hard', 40, 'back-left', d0('in front of me, on my left', 'at my back-left'), 'back-right'),
                       twin('hard', 'front-left', 'front-left'))
        self.assertEqual(r['cls'], 'c')

    def test_c_medium_ahead_side_swapped_only(self):
        r = C.classify(row('medium', 20, 'right', d0('ahead of me, slightly to my left', 'to my right'), 'back'),
                       twin('medium', 'left', 'left'))
        self.assertEqual(r['cls'], 'c')

    def test_c_medium_behind_band_flipped_only(self):
        r = C.classify(row('medium', 150, 'left', d0('behind me, on my left', 'to my left'), 'right'),
                       twin('medium', 'back', 'back'))
        self.assertEqual(r['cls'], 'c')

    def test_d_stated_forward_wrong(self):
        r = C.classify(row('easy', 70, 'left', d0('to my right', 'to my left'), 'right'), twin('easy', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('d', 'stated'))

    def test_d_twin_wrong_without_stated_forward(self):
        t = ('Step 2: standing at the bed and facing away from the door, the bag lies 41 degrees right of straight '
             'ahead, in front.\nSo the bag is at my front-right.')
        r = C.classify(row('hard', 40, 'front-right', t, 'back-right'), twin('hard', 'front-right', 'front-left'))
        self.assertEqual((r['cls'], r['sub']), ('d', 'twin'))

    def test_f_unparsed(self):
        r = C.classify(row('easy', 70, None, d0('to my left', 'to my right'), 'right'), twin('easy', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('f', 'unparsed'))

    def test_f_mapping(self):
        r = C.classify(row('medium', 90, 'back', d0('out to my left', 'to my right'), 'right'),
                       twin('medium', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('f', 'mapping'))
        self.assertTrue(r['conclusion_letter_mismatch'])

    def test_f_other(self):
        r = C.classify(row('medium', 90, 'back', d0('out to my left', 'at my back'), 'right'),
                       twin('medium', 'left', 'left'))
        self.assertEqual((r['cls'], r['sub']), ('f', 'other'))

    def test_revsi_phrase_is_a_mention(self):
        t = ('Step 2: standing at the bed and facing the opposite direction of the door, the bag lies 50 degrees left '
             'of straight ahead, a turn of less than 135 degrees.\nSo the bag is on my left.')
        r = C.classify(row('medium', 70, 'left', t, 'right'), twin('medium', 'left', 'left'))
        self.assertEqual((r['clause'], r['cls']), ('mention', 'b'))

    def test_bearing_180_is_not_a_turn(self):
        t = ('Step 2: standing at the bed and facing the door, the bag lies 179 degrees from straight ahead, '
             'a turn of at least 135 degrees.\nSo the bag is behind me.')
        self.assertEqual(C.clause_kind(t), 'none')

    def test_no_twin_candidates(self):
        r0 = row('medium', 0, 'right', d0('out to my right', 'to my right'), 'left')
        r0['label_provenance'] = {}
        r = C.classify(r0)
        self.assertEqual(r['cls'], 'b')
        self.assertEqual(sorted(map(tuple, r['forward_true'])), [('B', 'right'), ('O', 'right')])

    def test_pair_classes(self):
        self.assertEqual(C.pair_class('left', 'left'), 'unchanged')
        self.assertEqual(C.pair_class('back-right', 'front-left'), 'opposite')
        self.assertEqual(C.pair_class('front-right', 'front-left'), 'neither')
        self.assertEqual(C.pair_class('right', 'back'), 'neither')
        self.assertEqual(C.pair_class(None, 'back'), 'unparsed')

    def test_twelve_transitions(self):
        keys = set()
        for level, thetas in (('easy', (60, -60)), ('medium', (20, -20, 90, -90, 150, -150)), ('hard', (40, -40, 120, -120))):
            for th in thetas:
                rel = C.rel_from_bearing(th, level)
                keys.add((level, C.content_band(rel, level), C.content(C.half_turn(rel, level), level)))
        self.assertEqual(len(keys), 12)


@unittest.skipUnless(os.path.exists(os.path.join(M544, 'away/results/0/budget_2048.jsonl')), 'step-544 journals absent')
class TestStep544Agreement(unittest.TestCase):
    def test_pair_classes_match_f1f2(self):
        away = C.load(os.path.join(M544, 'away/results/0/budget_2048.jsonl'))
        toward = C.load(os.path.join(M544, 'forward/results/0/budget_2048.jsonl'))
        items = C.load(os.path.join(READK, 'evidence/A544.jsonl'))
        res, check = C.run(away, toward, items)
        self.assertEqual(check['prediction_mismatches'], 0)
        s = C.summarize(res, 't')
        self.assertEqual(s['pair_classes'], {'unchanged': 74, 'opposite': 41, 'neither': 35})
        sys.path.insert(0, READK)
        import f1f2
        self.assertEqual(f1f2.twins(items)['alike_pairs'], s['pair_classes']['unchanged'])
        # every correct away answer of A544 is class e, and accuracy per level is 38 / 20 / 6
        acc = {lv: 100.0 * s['by_level'][lv].get('e', 0) / s['by_level'][lv]['n'] for lv in C.LEVELS}
        self.assertEqual(acc, {'easy': 38.0, 'medium': 20.0, 'hard': 6.0})

    def test_labels_consistent_with_bearing(self):
        for r in C.load(os.path.join(M544, 'away/results/0/budget_2048.jsonl')):
            lv = C.level_of(r)
            f, src = C.true_forward(r, lv)
            self.assertEqual(src, 'bearing')
            self.assertEqual(C.content(f[0], lv), r['label_provenance']['backdir']['forward_answer_content'])
            self.assertEqual(C.content(C.half_turn(f[0], lv), lv), C.option_contents(r)[r['ground_truth']])


if __name__ == '__main__':
    unittest.main()
