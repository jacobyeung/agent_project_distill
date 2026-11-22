"""STAB dry check: every input exists with its registered sha256 and every key joins. Counts only; no score field is read."""
import collections
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script directory
import common as C  # noqa: E402


def main():
    inputs = C.verify(list(C.REG))
    inputs['score_nfa'] = C.item_score_fn()[1]
    camgt = sorted(C.CAMGT_DIR.glob('*.npz'))
    inputs['camgt_npz_dir'] = dict(path=str(C.CAMGT_DIR), files=len(camgt))
    tau = json.loads(C.TAU_JSON.read_text())
    inputs['tau_json'] = dict(path=str(C.TAU_JSON), sha256=C.sha(C.TAU_JSON))
    items = C.load_items()
    arms = C.load_arm_rows()
    joins = C.join(items, arms)
    direct_frames = json.loads(C.DIRECT_FRAMES.read_text()) if C.DIRECT_FRAMES.is_file() else None
    frames = C.frame_checks(items, arms, direct_frames)
    # Same frames and checkpoint should give the same own-head poses in the tower and own reads (evidence, not a gate).
    pose = {}
    for kind in C.TYPES:
        eq, dev = 0, []
        for i, r in arms['base'][kind].items():
            a, b = np.asarray(r['output']['heads']['pose9'], float), np.asarray(arms['own'][kind][i]['output']['heads']['pose9'], float)
            eq += bool(np.array_equal(a, b))
            dev.append(float(np.abs(a-b).max()))
        pose[kind] = dict(bit_equal=eq, of=len(dev), max_abs_diff_median=float(np.median(dev)), max_abs_diff_max=max(dev))
    flagged = set(tau['flags']['list'])
    caps = {c for c in tau['per_capture']}
    scenes = collections.Counter(it['scene'] for it in items.values() if it['question_type'] in C.TYPES)
    finish = {('%s|%s' % (arm, kind)): dict(collections.Counter(
        (r['output'].get('finish') if arm != 'direct' else r['finish_reason']) for r in rows.values()))
        for arm, per in arms.items() for kind, rows in per.items()}
    out = dict(schema='stab-drycheck-v1', note='counts only; no score field was read', inputs=inputs, joins=joins, frames=frames,
               own_vs_tower_pose9=pose, finish_counts=finish,
               items_on_k5=sum(s in caps for s in scenes.elements()), items_total=sum(scenes.values()),
               tau_deg=tau['tau_deg'], flagged_items={k: v['items'] for k, v in tau['flags']['items'].items()},
               flagged_items_check={k: sum(items[i]['scene'] in flagged for i in C.type_ids(items, k)) for k in C.TYPES},
               review_go_present=(C.STAB/'REVIEW_GO').exists(), status='pass')
    (C.STAB/'code/DRYCHECK.json').write_text(json.dumps(out, indent=1)+'\n')
    print(json.dumps({k: out[k] for k in ('joins', 'frames', 'own_vs_tower_pose9', 'items_on_k5', 'items_total', 'flagged_items', 'flagged_items_check', 'status')}, indent=1))


if __name__ == '__main__':
    main()
