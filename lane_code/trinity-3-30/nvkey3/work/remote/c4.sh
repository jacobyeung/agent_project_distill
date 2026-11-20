K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
echo "== $(date -u +%T) $(wc -l < out/60_v6bA_first30.jsonl) A, $(wc -l < out/61_v6bN_first30.jsonl) N, $(cat queue/62_v6bI_first30.jsonl 2>/dev/null | wc -l) I queued, $(cat out/62_v6bI_first30.jsonl 2>/dev/null | wc -l) I out, $(cat queue/62_v6bI_first30.jsonl.done 2>/dev/null | wc -l) caps chained; $(tail -1 v6b/chain.log)"
tail -3 runner.log | cut -c1-160; ls faults/; cat meter/METER.json; echo
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json, sys, collections
sys.path.insert(0, 'kit'); from score_v1 import parse
for fn in ('out/60_v6bA_first30.jsonl', 'out/61_v6bN_first30.jsonl'):
    c = collections.Counter(); toks = collections.defaultdict(list)
    for l in open(fn):
        r = json.loads(l); d = parse(r['text']); fam = r['meta']['family']; c[(fam, isinstance(d, dict), r.get('finish'))] += 1
        toks[fam].append(((r.get('usage') or {}).get('completion'), r.get('secs')))
    print(fn, dict(c)); print('  out tokens, secs', {f: v[:6] for f, v in toks.items()})
r = json.loads(open('out/61_v6bN_first30.jsonl').readline()) if sum(1 for _ in open('out/61_v6bN_first30.jsonl')) else None
if r: print('N sample', r['meta']['family'], repr(r['text'][:500]))
r = json.loads(open('out/60_v6bA_first30.jsonl').readline()); print('A sample', r['meta']['family'], repr(r['text'][:300]))
PY
