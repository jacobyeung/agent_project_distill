"""Q1: five verbatim step-200 traces per new form beside step 544's trace on the same item (Q1_EXAMPLES.md)."""
import json, re
rows = json.load(open('TRACES_DIST_544_200.json'))
m = {(r['step'], r['key']): r for r in rows}
def tmpl(r):
    T = set(r['templates'])
    if 'first_seen_frame' in T and 'nearest_to_farthest' in T: return 'REL'
    if 'gap_between_closest_points' in T: return 'PROC'
    return 'OTHER'
def pick(pred, n=5):
    out, seen = [], set()
    cand = [r for r in rows if r['step'] == '200' and pred(r)]
    for u in ('in', 'cm', 'ft', 'm', 'in', 'cm', 'ft', 'm', 'in', 'cm'):
        for r in cand:
            if r['unit'] == u and r['key'] not in seen:
                out.append(r); seen.add(r['key']); break
        if len(out) == n: break
    return out
groups = [
 ('F3 no call, stated estimate, relative-distance phrasing', lambda r: r['form'] == 'F3' and tmpl(r) == 'REL'),
 ('F3/F4 no call, procedure sentence ("find the X and the Y, then the gap between their closest points")', lambda r: r['form'] in ('F3', 'F4') and tmpl(r) == 'PROC'),
 ('F4 no call, qualitative sentence (no number before the answer)', lambda r: r['form'] == 'F4'),
 ('F2 call, conversion arithmetic, answer (unit-row phrasing)', lambda r: r['form'] == 'F2'),
]
L = ['# Q1 examples: step 200 (172744) beside step 544 (171253 read 1) on the same item', '',
     'Verbatim generated text (tool responses included as printed). Score = item MRA (0-1).', '']
for title, pred in groups:
    L += ['## ' + title, '']
    for r in pick(pred):
        b = m[('544', r['key'])]
        L += ['### %s (%s, truth %s %s; %s)' % (r['key'], r['unit'], r['gt'], r['unit'], r['question']), '',
              '- step 544: form %s, %d calls, answer %s, score %.2f' % (b['form'], b['ncalls'], b['answer'], b['score']),
              '```', b['text'], '```',
              '- step 200: form %s, %d calls, answer %s, score %.2f' % (r['form'], r['ncalls'], r['answer'], r['score']),
              '```', r['text'], '```', '']
open('Q1_EXAMPLES.md', 'w').write('\n'.join(L) + '\n')
print(len(L))
