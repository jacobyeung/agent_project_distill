"""Response-level price of each reader replacement on dev-S1 (CPU, before the GPU parity read).

Calls are held fixed at the scripted arm of job 170056 (one scripted program per item, the same
calls the model made on 149/150 distance items and every other item). Each variant recomputes
the responses those calls get, and the item is scored by the scripted arm's answer rule
(perception.script_answer: the last response, converted to the asked unit) with the unchanged
scorer evalpath.run.score_item. The scripted rule converts units; that is a pricing device that
isolates the backend change, never part of the reader (USER 2026-11-16: the model converts).

Variants: old (recorded responses; must reproduce the job's scripted scores)
          hook  (hook-only: identical by the token-parity proof)
          scale (+ scale head: camera responses recomputed exactly from the raw G3T cache, the
                 recorded own gravity and the head's scale; gap distance rescaled by s_new/s_old,
                 which E3 measured as near-linear; room area by (s_new/s_old)^2)
Selector and no-depth-cut variants need the grounding socket on dev-S1 masks (added later).
Usage: python -B price_devs1.py R1.json CLIP_TO_RAW.json direct_main.jsonl direct_camera.jsonl OUT.json [scale_json]
       scale_json: {clip: scale} from the scale head (omit for old/hook only).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449',
                str(ROOT / 'work/c8r/sj/orch_cd/evalx/work/milestone/native/out2')]


def family(t):
    return t


def tasks(paths):
    out = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            r = json.loads(line)
            out['devrows:' + r['id']] = r
    return out


def script_answer(task, calls):
    """perception.script_answer (C8r native/out2/perception.py:320) on a list of calls."""
    import perception as P
    return P.script_answer(task, dict(errors=sum(c.get('kind') == 'error' for c in calls), calls=calls))


def score(task, answer):
    from evalpath.run import score_item
    text = '<think>\n</think>\n\n' + (answer or '')
    return score_item(task, dict(text=text, finish='eos'))['score']


def main():
    r1, clipmap, main_items, cam_items, out = sys.argv[1:6]
    scales = json.loads(Path(sys.argv[6]).read_text()) if len(sys.argv) > 6 else None
    import numpy as np
    from e2e_reader import geometry as G
    from student_pilot.carrier_c1_decode import respond
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    T = tasks([main_items, cam_items])
    d = json.loads(Path(r1).read_text())
    raw = json.loads(Path(clipmap).read_text())
    geo_dir = Path(r1).parent / 'geometry'
    grav = {}
    for arm in ('unflagged', 'scripted'):
        for r in d['arms'][arm]:
            dec = r.get('decode')
            if dec and dec['heads'].get('gravity'):
                grav.setdefault(r['perception']['clip'], dec['heads']['gravity'])
    rows, recorded_check = [], []
    for r in d['arms']['scripted']:
        task = T[r['key']]
        typ = task['question_type']
        dec = r.get('decode')
        clip = r['perception']['clip']
        row = dict(key=r['key'], type=typ, room=r['room'], unit=r['question_unit'].get('unit'))
        if not dec:
            row.update(old=0.0, hook=0.0, scale=None, note='geometry refused in job (reviewed guard)')
            rows.append(row)
            continue
        calls = dec['calls']
        old = score(task, script_answer(task, calls))
        recorded_check.append(abs(old - r['scores']['answer']) < 1e-12)
        row.update(old=old, hook=old)
        if scales is not None and clip in scales:
            s_old = float(np.load(geo_dir / (clip + '.npz'))['scale'])
            s_new = float(scales[clip])
            ratio = s_new / s_old
            new_calls = []
            if typ.startswith('camera_'):
                z = np.load(raw[clip])
                g = G.from_tower(z['raw_pose'], z['anchor_slots'], z['frame_indices'], z['depth_grid'], z['grid_uv'],
                                 np.array(grav[clip]), s_new, z['source_hw'])
                own = G.camera_geometry(g)[0]
                for c in calls:
                    text, info = respond(c['call'], PrintedPointRegistry(), own)
                    new_calls.append(dict(c, response=text, kind=info.get('kind', c.get('kind'))))
            else:
                for c in calls:
                    body = c['response']
                    m = re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m', body)
                    if m:
                        body = 'distance %.2f m' % (float(m[1]) * ratio)
                    new_calls.append(dict(c, response=body))
                if typ == 'room_size_estimation':
                    new_calls = None  # room is unserved in the new reader (no room-area head)
            row.update(scale=None if new_calls is None else score(task, script_answer(task, new_calls)),
                       s_old=s_old, s_new=s_new)
        rows.append(row)
    summary = {}
    for typ in sorted({r['type'] for r in rows}):
        sel = [r for r in rows if r['type'] == typ]
        entry = dict(items=len(sel), old=100 * np.mean([r['old'] for r in sel]))
        if scales is not None:
            vals = [r['scale'] for r in sel if r.get('scale') is not None]
            entry['scale'] = 100 * np.mean([r['scale'] if r.get('scale') is not None else 0. for r in sel]) if vals else None
            entry['scale_unserved'] = sum(r.get('scale') is None for r in sel)
        summary[typ] = entry
    res = dict(summary=summary, recorded_scores_reproduced=all(recorded_check), checked=len(recorded_check), rows=rows)
    Path(out).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(dict(summary=summary, reproduced=res['recorded_scores_reproduced'], checked=len(recorded_check)), indent=1))


if __name__ == '__main__':
    main()
