"""Pack the selected head rows of assign.py with the sealed ground_rows.pack (brief 08 part B).

Inputs: the items and responses JSONL given to assign.run, and its SELECTED.jsonl. For every selected head decision
the item is re-decided (the decision must still be head), the record is packed with the builder's membership flags
and the provenance below, and the packed row re-renders under ground_rows.render_ground. Recovery and direct
selections are listed for the joiner (tree_rebuild4) and not packed here.
Output: HEAD_ROWS.jsonl, OTHER_SELECTED.jsonl, ROWS_MANIFEST.json (counts per type, sha256 of every file and input).
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assign as A


def render(packed):
    if str(A.TREE) not in sys.path:
        sys.path.insert(0, str(A.TREE))
    from student_pilot import ground_rows
    target, spans, _ = ground_rows.render_ground(packed['events'], packed['answer'])
    return target, spans


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def pack_head(item, response, eligibility):
    decision, reason = A.decide(item, response, eligibility)
    if decision != 'head':
        raise ValueError(f"{item['qid']} is no longer head: {decision}:{reason}")
    provenance = dict(builder='b08_headrows/code/headrows/build_rows.py', assignment='head', reason=reason,
                      assign_sha256=A.sha256(A.__file__), pipeline=response['pipeline'],
                      pipeline_sha256=response['pipeline_sha256'], replay=response['record']['replay'],
                      selected_instances=response['selected'], gt_instances=item['gt_instances'],
                      dataset=item['dataset'], scene=item['scene'], room_key=item['room_key'])
    packed = A.sealed_pack(item, response['record'], head=True)
    packed['provenance'] = provenance
    packed['dataset'], packed['scene'] = item['dataset'], item['scene']
    if 'student_input' in item:
        packed['student_input'] = item['student_input']
    if render(packed) != (packed['target'], packed['tool_output_spans']):
        raise ValueError(item['qid'] + ' packed row does not re-render')
    return packed


def run(items_path, responses_path, selected_path, out_dir, auth=A.AUTH):
    eligibility = A.Eligibility(auth)
    items = {d['qid']: d for d in load(items_path)}
    responses = {d['qid']: d for d in load(responses_path)}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with open(out / 'HEAD_ROWS.jsonl', 'w') as heads, open(out / 'OTHER_SELECTED.jsonl', 'w') as other:
        for sel in load(selected_path):
            if sel['decision'] == 'head':
                row = pack_head(items[sel['qid']], responses[sel['qid']], eligibility)
                heads.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')
            else:
                other.write(json.dumps(sel, sort_keys=True) + '\n')
            counts[f"{sel['type']}|{sel['decision']}"] += 1
    manifest = dict(inputs={str(p): A.sha256(p) for p in (items_path, responses_path, selected_path)},
                    code={Path(f).name: A.sha256(f) for f in (__file__, A.__file__)}, counts=dict(counts),
                    outputs={n: A.sha256(out / n) for n in ('HEAD_ROWS.jsonl', 'OTHER_SELECTED.jsonl')})
    (out / 'ROWS_MANIFEST.json').write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    for a in ('items', 'responses', 'selected', 'out'):
        p.add_argument('--' + a, required=True)
    a = p.parse_args()
    print(json.dumps(run(a.items, a.responses, a.selected, a.out)['counts'], indent=1))
