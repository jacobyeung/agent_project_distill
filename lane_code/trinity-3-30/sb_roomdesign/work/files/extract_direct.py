"""Write the direct-answer file the room pricing scorer pairs against.

Usage: python extract_direct.py ROOM134_JSON JOURNAL_ITEMS_JSONL [more journals] --out direct_room134.json
Reads the accepted routed read's room items (h1-items-v1 `room134.json`) and the read's journal(s),
takes the number after the closing think tag as the direct answer, and refuses unless the official
MRA of that number equals the score the reader stored for every item. No model, no GPU.
"""
import argparse, hashlib, json, math, re, sys

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def mra(pred, gt, start=0.5, end=0.95, interval=0.05):
    # Same arithmetic as evalpath/official.py official_mra.
    if pred is None or gt is None or not math.isfinite(pred) or not math.isfinite(gt):
        return 0.0
    if gt == 0.0:
        return 1.0 if pred == 0.0 else 0.0
    num_pts = int((end - start) / interval + 2)
    conf = [start + i * (end - start) / (num_pts - 1) for i in range(num_pts)]
    rel_err = abs(pred - gt) / abs(gt)
    return sum(1.0 if rel_err <= (1.0 - c) else 0.0 for c in conf) / len(conf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('items'); ap.add_argument('journals', nargs='+'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    manifest = json.load(open(a.items))
    items = {i['id']: i for i in manifest['items'] if i['question_type'] == 'room_size_estimation'}
    rows, seen = [], set()
    for path in a.journals:
        for line in open(path):
            r = json.loads(line)
            if r['id'] not in items or r.get('complete') is not True:
                continue
            if r['id'] in seen:
                sys.exit('duplicate item ' + r['id'])
            seen.add(r['id'])
            it, out = items[r['id']], r['output']
            m = re.search(r'</think>\s*(-?[0-9]+(?:\.[0-9]+)?)', out['text'])
            pred = float(m.group(1)) if m else None
            gt = float(it['answer'])  # the label the reader scores (metric mra_answer)
            released = it.get('released_answer')
            unit = 'ft2' if re.search(r'square f(ee|oo)t', it['question'], re.I) else 'm2'
            if abs(mra(pred, gt) - out['scores']['answer']) > 1e-9:
                sys.exit('parsed answer does not reproduce the stored score for ' + r['id'])
            rows.append(dict(id=r['id'], set='R0-dev' if it.get('r0_split') == 'R0-dev' else 'dev-S1',
                             dataset=it['dataset'], room=it['room_key'], unit=unit,
                             gt=gt, released_label=None if released is None else float(released), direct=pred, direct_mra=out['scores']['answer'],
                             calls=len(out['calls'].get('records', [])), finish=out['finish']))
    if seen != set(items):
        sys.exit('journal covers %d of %d room items' % (len(seen), len(items)))
    rows.sort(key=lambda r: r['id'])
    json.dump(dict(schema='room-direct-v1', items_sha256=sha(a.items),
                   journals={p: sha(p) for p in a.journals}, rows=rows), open(a.out, 'w'), indent=1)
    for name in ('R0-dev', 'dev-S1'):
        s = [r for r in rows if r['set'] == name]
        print(name, len(s), 'direct MRA %.2f' % (100 * sum(r['direct_mra'] for r in s) / len(s)))

if __name__ == '__main__':
    main()
