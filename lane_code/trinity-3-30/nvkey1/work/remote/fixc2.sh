set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $K
date -u +%T; touch $K/ctl/STOP
for i in $(seq 1 60); do pgrep -f "kit/nvrun.py" >/dev/null || break; sleep 5; done
echo "runner gone after $((i*5)) s: $(pgrep -f kit/nvrun.py | wc -l) left"; tail -3 $K/runner.log
mv $K/queue/40_c2audit.jsonl $K/queue/40_c2audit.jsonl.bad_heldout_filter
cat > $K/kit/c2_jobs.py <<'PYEOF'
"""nvkey1 C2: pointing-row audit tasks. One call = up to CHUNK rows of one clip, each row one frame (a red ring at the row's point for a visible
row; no ring for an absent row) and its claim. Rows: the pointing store rows whose frame is on this node, minus the K1-heldout removal list.
usage: c2_jobs.py OUT.jsonl MODEL EFFORT [CHUNK=40] [ROWS=all|path to a json list of store indices]  (C1_EXTRA env adds request fields)"""
import json, os, sys, sqlite3, random, collections
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
STORE = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
HELD = '/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl'
ROOTS = ['/scratch/jjyeung/k1_frames', '/scratch/jjyeung/devs1_frames']
PROMPT = ('You are auditing labels of a pointing dataset. Each row below shows one video frame of an indoor room and one claim about it.\n'
          '- A "point" row has a red ring drawn on the image. Its claim: the centre of the ring lies on a visible part of an object of the named kind.\n'
          '- An "absent" row has no ring. Its claim: no object of the named kind is visible anywhere in the image.\n'
          'Judge every claim from its image alone, and answer for each row:\n'
          '"present": is at least one object of the named kind visible in the image, fully or partly? true or false.\n'
          '"on_object": point rows only: is the centre of the ring on a visible part of an object of the named kind? true or false; null for absent rows.\n'
          '"name_fits": point rows only: would most people call the object under the centre of the ring by the given name or a close synonym? true or false; null for absent rows.\n'
          '"point": when present is true and the claim is wrong (an absent row, or on_object false), one point on a visible part of the named object as [x, y] '
          'in 0-1000 image coordinates (x = 0 left edge, 1000 right edge; y = 0 top edge, 1000 bottom edge); otherwise null.\n'
          'Reply with one JSON object and nothing else: {{"<row id>": {{"present": ..., "on_object": ..., "name_fits": ..., "point": ...}}, ...}} with all {n} row ids.')
def frame_path(sha):
    for r in ROOTS:
        p = '%s/%s/%s.png' % (r, sha[:2], sha)
        if os.path.exists(p): return p
def held_ids():
    s = set()
    if os.path.exists(HELD):
        for l in open(HELD):
            try:
                d = json.loads(l); k = d.get('row_key') or d.get('qid')
                if k: s.add(str(k))
            except Exception: pass
    return s
def load_rows(only=None):
    c = sqlite3.connect('file:%s?mode=ro' % STORE, uri=True); held = held_ids(); out = []; nheld_rows = [0]
    for i, s in c.execute('select i,row from rows'):
        if only is not None and i not in only: continue
        d = json.loads(s); p = d['pointing']; f = frame_path(p.get('rgb_sha256') or '')
        if not f: continue
        if d.get('qid') in held: nheld_rows[0] += 1; continue
        out.append(dict(i=i, qid=d.get('qid'), scene=d['scene'], dataset=d['dataset'], kind=p['kind'], label=p['label'], frame=p['frame'], area=p.get('area_fraction') or 0.0,
                        stratum=p.get('stratum'), uv=(p.get('selected') or {}).get('uv'), path=f, canonical=(d.get('provenance') or {}).get('canonical_scene')))
    print('held-out list keys', len(held), 'local rows dropped as K1-heldout', nheld_rows[0])
    return out, len(held)
def main():
    out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    only = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 and sys.argv[5] != 'all' else None
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); tag = model.split('/')[-1]
    rows, nheld = load_rows(only); byc = collections.defaultdict(list)
    for r in rows: byc[r['scene']].append(r)
    rng = random.Random(20261120); n = 0; meta_rows = {}
    with open(out, 'a') as f:
        for sc in sorted(byc):
            rs = byc[sc][:]; rng.shuffle(rs)
            for j in range(0, len(rs), chunk):
                part = rs[j:j + chunk]; content = [{'text': PROMPT.format(n=len(part))}]
                for r in part:
                    rid = 'r%d' % r['i']
                    if r['kind'] == 'gt_absent':
                        content += [{'text': 'Row %s (absent row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640}]
                    else:
                        content += [{'text': 'Row %s (point row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640, 'mark': r['uv']}]
                f.write(json.dumps({'id': 'c2_%s_%d_%s' % (sc, j // chunk, tag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                                    'content': content, 'meta': {'scene': sc, 'rows': [r['i'] for r in part]}}) + '\n'); n += 1
                for r in part: meta_rows[r['i']] = {k: r[k] for k in ('qid', 'scene', 'dataset', 'kind', 'label', 'frame', 'area', 'stratum', 'uv', 'canonical')}
    json.dump(meta_rows, open(K + '/c2_rows_meta.json', 'w'))
    print('rows', len(rows), 'clips', len(byc), 'tasks', n, 'heldout ids in list', nheld, 'kinds', dict(collections.Counter(r['kind'] for r in rows)))
if __name__ == '__main__': main()
PYEOF
Q=$K/queue/41_c2audit.jsonl
$P -B kit/c2_jobs.py $Q.tmp gcp/google/gemini-4-argon high 40 && $P -B kit/c2_jobs.py $Q.tmp openai/openai/gpt-6.2-astra high 40 && mv $Q.tmp $Q
wc -l $Q; grep -c . $K/out/40_c2audit.jsonl 2>/dev/null
mv $K/ctl/STOP $K/ctl/STOP.done.$(date +%s)
CA=/etc/pki/tls/certs/ca-bundle.crt
tmux kill-session -t nvk1_run 2>/dev/null; sleep 1
tmux new-session -d -s nvk1_run "cd $K && SSL_CERT_FILE=$CA NVK=$K $P -B kit/nvrun.py 3600 </dev/null >>$K/runner.stdout 2>&1" </dev/null >/dev/null 2>&1
sleep 15; tmux ls | grep nvk1; tail -6 $K/runner.log; date -u +%T
