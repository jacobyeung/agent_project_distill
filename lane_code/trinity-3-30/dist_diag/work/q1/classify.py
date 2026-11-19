"""Q1: classify the 150 dev-S1 routed distance traces at step 544 and step 200 by form and template.
Forms: F1 call->answer; F2 call->conversion arithmetic->answer; F3 no call, stated estimate (a number in the reasoning);
F4 no call, qualitative sentence (no number before the answer); F5 other (capped, empty, unparsed).
Templates (phrasing tags, independent of form) are regex hits in the generated text, used to match row families."""
import json, re, sys, statistics as st
from collections import Counter, defaultdict
from load import *
a, bd, ba, items, src = load_all()
keys = sorted(k for k, i in items.items() if i['question_type'] == S.DISTANCE)
NUM = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
CONV = re.compile(r'(?i)(convert\w*|\b(?:x|\*|×)\s*(?:3\.28\d*|39\.3\d*|100|0\.3048|0\.0254|12)\b|/\s*(?:0\.3048|0\.0254)\b)')
TEMPL = {
 'first_seen_frame': r'first seen in frame',
 'nearest_to_farthest': r'nearest[- ]to[- ]farthest',
 'candidates_ordered': r'candidates ordered',
 'question_asks_for': r'the question asks for',
 'i_find_it_to_be': r'I find (?:it|that|the gap|the distance)[^.\n]{0,60}to be',
 'gap_between_closest_points': r'then the (?:gap|shortest distance|spacing|distance) between (?:their closest points|them)',
 'the_gap_is': r'\bthe gap is\b',
 'stand_at_facing': r'when I stand at',
 'box_distance_is': r'The box distance is',
 'grid_5cm_two_objects': r'5 cm grid over the two objects',
 'grid_both_objects': r'on a grid over both objects',
 'converting_to': r'Converting to (?:feet|inches|centimet)',
 'ground_boxes_intro': r'I will ground the boxes',
 'locate_line': r'(?m)^Locate',
 'relate_line': r'(?m)^Relate',
 'step_n': r'(?m)^Step \d+:',
}
TEMPL = {k: re.compile(v) for k, v in TEMPL.items()}
def think(t):
    return t.split('</think>', 1)[0]
def strip_tools(t):
    return re.sub(r'<tool_response>.*?</tool_response>', '', t, flags=re.S)
def answer(out):
    return sc.answer_text(out)
def classify(out):
    rs = sc.records(out); t = out.get('text', ''); fin = out.get('finish')
    th = strip_tools(think(t))
    if fin in ('max_calls', 'max_new_tokens', 'length') or not t.strip():
        return 'F5', rs
    if rs:
        post = strip_tools(t[t.rfind('</tool_response>'):]) if '</tool_response>' in t else th
        return ('F2' if CONV.search(post) else 'F1'), rs
    nums = re.findall(NUM + r'\s*(?:m\b|meters?|metres?|cm|centimet\w*|feet|foot|ft\b|inch\w*|in\b)', th)
    if nums: return 'F3', rs
    if re.search(r'\d', re.sub(r'frame \d+|Step \d+', '', th)): return 'F3', rs
    return 'F4', rs
rows = []
for step, R in (('544', bd), ('200', a)):
    for k in keys:
        out = R[k]['output']; it = items[k]; form, rs = classify(out)
        t = out.get('text', '')
        rows.append(dict(key=k, step=step, unit=unit(it['question']), room=it['room_key'], gt=float(it['ground_truth']),
            question=it['question'], form=form, ncalls=len(rs), kinds=dict(Counter(sc.signature(r['call'])[0] for r in rs)),
            finish=out.get('finish'), answer=answer(out), score=float(sc.accuracy(out, it)['task_accuracy']),
            templates=sorted(n for n, rx in TEMPL.items() if rx.search(strip_tools(t))), tokens=len(out.get('tokens') or []), text=t))
json.dump(rows, open('TRACES_DIST_544_200.json', 'w'))
by = defaultdict(Counter)
for r in rows: by[r['step']][(r['form'], r['unit'])] += 1
units = ['m', 'ft', 'in', 'cm']; forms = ['F1', 'F2', 'F3', 'F4', 'F5']
for step in ('544', '200'):
    print('step', step, 'form x unit (m ft in cm | total)')
    for f in forms:
        c = [by[step][(f, u)] for u in units]; print('  %s %s | %d' % (f, ' '.join('%3d' % x for x in c), sum(c)))
# transitions
tr = Counter(); m = {(r['step'], r['key']): r for r in rows}
for k in keys: tr[(m[('544', k)]['form'], m[('200', k)]['form'])] += 1
print('transitions 544->200', dict(tr))
