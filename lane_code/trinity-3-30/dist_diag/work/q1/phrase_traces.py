"""Q2: which family's phrasing each step-200 no-call trace copies (phrase ids from q2/phrases.py)."""
import json, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, '../q2'); from phrases import PH
rows = json.load(open('TRACES_DIST_544_200.json'))
FAM = {  # family -> phrase ids specific to it (checked against PHRASE_BY_FAMILY.json)
 'relative_distance': ['candidates_ordered_n2f', 'n2f_order_from', 'from_nearest_to_farthest', 'q_asks_closest', 'step1_find_first_seen'],
 'direction_facing': ['find_x_and_y_then', 'i_stand_at', 'i_keep_that', 'q_has_me', 'so_i_find'],
 'vsti_relative': ['take_camera_viewpoint', 'locate_first_seen'],
 'away_revsi': ['opposite_direction'],
 'room_traced': ['seen_line', 'farthest_apart', 'to_the_side', 'floor_area'],
 'first_seen_frame': ['first_appears_in_frame'],
 'counting_procedure': ['count_once'],
 'units_feet': ['converting_to', 'grid_both_objects'],
 'routing_metre': ['ground_boxes', 'box_distance_is'],
}
def strip(t): return re.sub(r'<tool_response>.*?</tool_response>', '', t, flags=re.S)
out = {}
for step in ('544', '200'):
    sel = [r for r in rows if r['step'] == step and r['form'] in ('F3', 'F4')]
    ph = Counter(); fam = Counter(); excl = Counter(); combos = Counter()
    for r in sel:
        t = strip(r['text']).split('</think>')[0]
        hits = set(p for p, rx in PH.items() if rx.search(t)); ph.update(hits)
        fs = sorted(f for f, ps in FAM.items() if hits & set(ps)); fam.update(fs); combos['+'.join(fs) or 'none'] += 1
        if len(fs) == 1: excl[fs[0]] += 1
    out[step] = dict(n=len(sel), phrase=dict(ph), family=dict(fam), family_exclusive=dict(excl), combos=dict(combos))
    print('step', step, 'no-call traces', len(sel)); print('  family (any phrase):', dict(fam)); print('  exclusive:', dict(excl)); print('  combos:', dict(combos)); print('  phrases:', dict(ph))
json.dump(out, open('NOCALL_PHRASE_ATTRIBUTION.json', 'w'), indent=1)
