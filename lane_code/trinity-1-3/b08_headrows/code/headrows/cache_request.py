"""Training items the response cache must read so that about 2,000 head rows per type survive (brief 08 part B).

Source: rows_a2's A2 VQA store (read only). Items pass assign.Eligibility; per type the count is
ceil(2000 / (head share on dev-S1 x MASK_PASS)), capped by availability, with at most PER_ROOM items per
(type, physical room), deterministic order sha256(seed:qid). Absolute distance is not in this store (routing
store) and its minority form is direct, so it is not requested here.
"""
import hashlib
import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assign as A

STORE = '/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v1/vqa/rows.sqlite'
STORE_SHA = '863dd608ff0ca741aa73db5d81a70d7d420fd13cb40321934f8dbf7a46515c82'
# head share per item on the dev-S1 program arm with masks assumed to match (out/PARTB_PREP.md dry run)
HEAD_SHARE = {'object_counting': 0.34, 'object_rel_distance': 0.42, 'object_rel_direction_medium': 0.66,
              'object_rel_direction_hard': 0.66}
MASK_PASS = 0.5  # assumed share of right answers whose masks also match GT; unmeasured
PER_ROOM = 12
SEED = 'b08-cache-20261116'


def main(out):
    if A.sha256(STORE) != STORE_SHA:
        raise ValueError('store sha differs')
    e = A.Eligibility()
    want = {t: math.ceil(A.MAX_CAP / (s * MASK_PASS)) for t, s in HEAD_SHARE.items()}
    pool = defaultdict(list)
    con = sqlite3.connect(f'file:{STORE}?mode=ro&immutable=1', uri=True)
    for i, row in con.execute('select i, row from rows'):
        d = json.loads(row)
        t = d.get('question_type')
        if t not in want:
            continue
        it = dict(qid=d['qid'], type=t, dataset=d['dataset'], scene=d['scene'])
        if e.reason(it) is None:
            pool[t].append(dict(it, room_key=it['room_key'], store_i=i, question=d['student_input'].get('question'),
                                options=d['student_input'].get('options') or d.get('options') or [], answer=d['answer']))
    chosen, per_room, summary = [], Counter(), {}
    for t, items in sorted(pool.items()):
        items.sort(key=lambda x: hashlib.sha256(f"{SEED}:{x['qid']}".encode()).hexdigest())
        picked = []
        for x in items:
            if len(picked) >= want[t]:
                break
            if per_room[(t, x['room_key'])] < PER_ROOM:
                per_room[(t, x['room_key'])] += 1
                picked.append(x)
        chosen += picked
        summary[t] = dict(eligible=len(items), wanted=want[t], requested=len(picked),
                          rooms=len({x['room_key'] for x in picked}))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'CACHE_REQUEST_ITEMS.jsonl', 'w') as f:
        for x in chosen:
            f.write(json.dumps(x, sort_keys=True, ensure_ascii=False) + '\n')
    manifest = dict(store=STORE, store_sha256=STORE_SHA, code_sha256=A.sha256(__file__), assign_sha256=A.sha256(A.__file__),
                    seed=SEED, per_room=PER_ROOM, mask_pass_assumed=MASK_PASS, head_share=HEAD_SHARE, summary=summary,
                    items_sha256=A.sha256(out / 'CACHE_REQUEST_ITEMS.jsonl'), total=len(chosen))
    (out / 'CACHE_REQUEST_MANIFEST.json').write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


if __name__ == '__main__':
    print(json.dumps(main(sys.argv[1]), indent=1))
