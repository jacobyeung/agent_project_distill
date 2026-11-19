"""Q2: phrase attribution. PH maps a phrase id to a regex. (1) For each store-v7 family (rows kept after n.json + z.json),
count rows whose target matches each phrase. (2) The unit rows (packed.jsonl, 747) likewise. Output PHRASE_BY_FAMILY.json."""
import sqlite3, json, re, sys
from collections import defaultdict, Counter
PH = {
 'step1_find_first_seen': r'Step 1: find the [^,\n]{1,40}, first seen in frame \d+',
 'find_first_seen_any': r'find the [^,\n]{1,40}, first seen in frame \d+',
 'candidates_ordered_n2f': r'candidates ordered nearest to farthest',
 'n2f_order_from': r'nearest-to-farthest order from',
 'from_nearest_to_farthest': r'from nearest to farthest from',
 'q_asks_closest': r'[Tt]he question asks (?:for the closest|me to choose)',
 'q_asks_for_the': r'[Tt]he question asks for the',
 'find_x_and_y_then': r'find the [^.\n]{1,40} and the [^.\n]{1,40}, then',
 'i_stand_at': r'I stand at',
 'i_keep_that': r'I keep that',
 'q_has_me': r'[Tt]he question has me',
 'so_i_find': r'So I find',
 'i_find': r'\bI find\b',
 'take_camera_viewpoint': r'take the camera viewpoint',
 'locate_first_seen': r'locate the [^,\n]{1,40}, first seen in frame',
 'opposite_direction': r'opposite direction',
 'seen_line': r'(?m)^Seen:',
 'farthest_apart': r'farthest apart',
 'to_the_side': r'to the side|off to the side',
 'floor_area': r'floor area',
 'first_appears_in_frame': r'first appears in frame',
 'count_once': r'count (?:it|each) once|find each distinct',
 'converting_to': r'Convert(?:ing|ed)? to (?:feet|inches|centimet)',
 'grid_both_objects': r'on a grid over both objects',
 'ground_boxes': r'I will ground the boxes',
 'box_distance_is': r'The box distance is',
 'estimate_from_frames': r'from the frames',
 'step_numbering': r'(?m)^Step \d+:',
}
PH = {k: re.compile(v) for k, v in PH.items()}
if __name__ == '__main__':
    N = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json'; Z = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json'
    drop = set(json.loads(l)['row_key'] for p in (N, Z) for l in open(p) if l.strip())
    fam = defaultdict(Counter); rows = Counter()
    con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
    for (row,) in con.execute('select row from rows'):
        r = json.loads(row)
        if r.get('qid') in drop: continue
        k = r.get('question_type') or r.get('category'); tg = r.get('target') or ''
        rows[k] += 1
        for p, rx in PH.items():
            if rx.search(tg): fam[k][p] += 1
    for l in open('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl'):
        r = json.loads(l); tg = r.get('target') or ''
        k = 'units_p_' + ('in' if '(in inches)' in r['question'] else 'ft'); rows[k] += 1
        for p, rx in PH.items():
            if rx.search(tg): fam[k][p] += 1
    json.dump(dict(rows=rows, hits={k: dict(v) for k, v in fam.items()}), open('PHRASE_BY_FAMILY.json', 'w'), indent=1, sort_keys=True)
    print('done', sum(rows.values()))
