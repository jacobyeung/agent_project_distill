"""Independent row-level review of the pointing Locate store against the original."""
from collections import Counter, defaultdict
import json
import re
import sqlite3
import sys

OLD = '/scratch/jjyeung/orch_n30/fb_pack/in/pointing/rows_c09bb5ca.sqlite'
NEW = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
OUT = '/scratch/jjyeung/orch_n30/fb_pack/pointrev/work/check_rows.json'

Q = re.compile(r'^Point to the (.+) in frame (\d+)\. Output the point as JSON \{"point_2d": \[x, y\]\} '
               r'with integer coordinates on a 0-1000 grid of that frame\. If there is no (.+) in frame (\d+), '
               r'output \{"point_2d": null\}\.$')
THINK = re.compile(r'^<think>\n(.*)\n</think>\n\n(.*)$', re.S)
VIS = re.compile(r'^Locate the (.+) in frame (\d+)\.$')
ABS = re.compile(r'^Locate the (.+) in frame (\d+): it is not visible in that frame\.$')
NUMWORDS = re.compile(r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|first|second|third|'
                      r'half|single|double|pair|dozen|x|y|px|pixel|pixels|coordinate|coordinates|left|right|top|bottom|'
                      r'center|centre|upper|lower|corner|point)\b', re.I)


def ro(p):
    return sqlite3.connect(f'file:{p}?mode=ro', uri=True)


def main():
    o, n = ro(OLD), ro(NEW)
    assert o.execute('select sql from sqlite_master').fetchall() == n.execute('select sql from sqlite_master').fetchall()
    problems = defaultdict(list)
    label_digit, label_numword, kinds = [], [], Counter()
    by_frame = defaultdict(list)
    labels = Counter()
    rows = 0
    for (i0, r0, t0), (i1, r1, t1) in zip(o.execute('select i,row,target from rows order by i'),
                                         n.execute('select i,row,target from rows order by i'), strict=True):
        assert i0 == i1 == rows, (i0, i1, rows)
        rows += 1
        if t0 != t1:
            problems['aux_target_changed'].append(i0)
        a, b = json.loads(r0), json.loads(r1)
        # (1) byte diff: the only differing span must lie inside the target string literal.
        old_lit, new_lit = json.dumps(a['target']), json.dumps(b['target'])
        key = '"target": '
        p0 = r0.find(key + old_lit)
        if p0 < 0 or r0.count(key + old_lit) != 1 or r0.find(key + '"') != p0:
            problems['target_locate_old'].append(i0); continue
        start = p0 + len(key)
        if r1[:start] != r0[:start] or r1[start + len(new_lit):] != r0[start + len(old_lit):] or r1[start:start + len(new_lit)] != new_lit:
            problems['bytes_outside_target'].append(i0)
        if list(a) != list(b) or {k: v for k, v in a.items() if k != 'target'} != {k: v for k, v in b.items() if k != 'target'}:
            problems['fields_outside_target'].append(i0)
        # target structure
        m0, m1 = THINK.match(a['target']), THINK.match(b['target'])
        if not (m0 and m0[1] == '' and a['target'].startswith('<think>\n\n</think>\n\n')):
            problems['old_think_not_empty'].append(i0)
        if not m1:
            problems['new_target_shape'].append(i0); continue
        body, ans_new = m1[1], m1[2]
        ans_old = a['target'][len('<think>\n\n</think>\n\n'):]
        if ans_new.encode() != ans_old.encode():
            problems['answer_bytes_changed'].append(i0)
        if '\n' in body or b['target'].count('<think>') != 1 or b['target'].count('</think>') != 1:
            problems['not_one_line'].append(i0)
        # (2) label/frame vs question
        q = b['student_input']['question']
        mq = Q.match(q)
        if not mq or mq[1] != mq[3] or mq[2] != mq[4]:
            problems['question_parse'].append(i0); continue
        qlabel, qframe = mq[1], int(mq[2])
        p = b['pointing']
        if p['label'] != qlabel or p['frame'] != qframe:
            problems['pointing_vs_question'].append(i0)
        ans = json.loads(ans_new)
        if list(ans) != ['point_2d']:
            problems['answer_keys'].append(i0); continue
        pt = ans['point_2d']
        mv, ma = VIS.match(body), ABS.match(body)
        if pt is None:
            if not ma: problems['null_without_not_visible'].append(i0)
            else:
                if ma[1] != qlabel or int(ma[2]) != qframe or ma[2] != str(qframe): problems['label_frame_mismatch'].append(i0)
        else:
            if not mv: problems['point_with_not_visible_or_other'].append(i0)
            else:
                if mv[1] != qlabel or int(mv[2]) != qframe or mv[2] != str(qframe): problems['label_frame_mismatch'].append(i0)
            if 'not visible' in body: problems['point_but_not_visible'].append(i0)
        # (6) consistency of answer with GT metadata
        absent_kind = p['kind'] == 'gt_absent'
        if absent_kind != (pt is None):
            problems['kind_vs_answer'].append(i0)
        uv = p['selected']['uv']
        if (uv is None) != (pt is None) or (uv is not None and list(uv) != list(pt)):
            problems['selected_uv_vs_answer'].append(i0)
        if absent_kind and p['area_fraction'] != 0.0:
            problems['absent_nonzero_area'].append(i0)
        if not absent_kind and not (p['area_fraction'] >= 0.002):
            problems['visible_tiny_area'].append(i0)
        if pt is not None and not all(isinstance(v, int) and 0 <= v <= 1000 for v in pt):
            problems['point_range'].append(i0)
        if not (1 <= qframe <= len(b['student_input']['frames'])):
            problems['frame_range'].append(i0)
        # (3) digits in think block
        digits = re.findall(r'\d+', body)
        expect = re.findall(r'\d+', qlabel) + [str(qframe)]
        if digits != expect:
            problems['unexpected_digits'].append(i0)
        if pt is not None and any(str(v) in digits and str(v) != str(qframe) and str(v) not in re.findall(r'\d+', qlabel) for v in pt):
            problems['coordinate_in_think'].append(i0)
        if re.search(r'\d', qlabel):
            label_digit.append({'i': i0, 'qid': b['qid'], 'label': qlabel, 'frame': qframe, 'think': body})
        rest = body.replace(qlabel, '', 1)
        if NUMWORDS.search(rest):
            problems['numword_outside_label'].append(i0)
        if NUMWORDS.search(qlabel):
            label_numword.append({'i': i0, 'label': qlabel, 'words': NUMWORDS.findall(qlabel)})
        if re.search(r'[^a-z0-9 \-/\'.,&()]', qlabel):
            problems['label_odd_chars'].append((i0, qlabel))
        if qlabel != qlabel.strip() or '  ' in qlabel or re.match(r'(the|a|an) ', qlabel, re.I):
            problems['label_article_or_space'].append((i0, qlabel))
        labels[qlabel] += 1
        kinds[(b['dataset'], p['kind'])] += 1
        by_frame[(b['dataset'], b['scene'], qframe)].append((i0, qlabel, pt, p.get('instance_id'), p['kind']))
    # (6) cross-row: same scene/frame/label with contradicting answers; absent label substring of a visible label.
    contradictions, near = [], []
    for key, items in by_frame.items():
        vis = {lab for _, lab, pt, _, _ in items if pt is not None}
        for i0, lab, pt, _, _ in items:
            if pt is None and lab in vis:
                contradictions.append({'i': i0, 'key': key, 'label': lab,
                                       'visible_rows': [j for j, l2, p2, _, _ in items if l2 == lab and p2 is not None]})
            if pt is None:
                for v in vis:
                    if v != lab and re.search(r'\b' + re.escape(lab) + r'\b', v):
                        near.append({'i': i0, 'key': list(key), 'absent': lab, 'visible_label_same_frame': v,
                                     'visible_rows': [j for j, l2, p2, _, _ in items if l2 == v and p2 is not None]})
    dups = Counter((k, lab) for k, items in by_frame.items() for _, lab, _, _, _ in items)
    dup_list = [[list(k), lab, n_] for (k, lab), n_ in dups.items() if n_ > 1]
    res = {'rows': rows, 'kinds': {f'{d}/{k}': v for (d, k), v in kinds.items()},
           'problems': {k: (len(v), v[:50]) for k, v in problems.items()},
           'label_digit_rows': label_digit, 'label_numword_rows': label_numword,
           'same_frame_label_contradictions': contradictions, 'absent_label_inside_visible_label_same_frame': near,
           'duplicate_scene_frame_label': dup_list[:50], 'duplicate_count': len(dup_list),
           'n_labels': len(labels)}
    with open(OUT, 'w') as f:
        json.dump(res, f, indent=1, default=str)
    print(json.dumps({k: (v if k != 'problems' else {a: c[0] for a, c in v.items()}) for k, v in res.items()
                      if k not in ('label_digit_rows', 'label_numword_rows', 'same_frame_label_contradictions',
                                   'absent_label_inside_visible_label_same_frame', 'duplicate_scene_frame_label')}, default=str))
    print('label_digit', len(label_digit), [(r['i'], r['label']) for r in label_digit])
    print('label_numword', len(label_numword), sorted({r['label'] for r in label_numword}))
    print('contradictions', len(contradictions), 'near', len(near), 'dups', len(dup_list))


if __name__ == '__main__':
    main()
