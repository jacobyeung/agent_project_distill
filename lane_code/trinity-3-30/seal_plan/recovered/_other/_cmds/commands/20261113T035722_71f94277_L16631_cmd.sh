<!-- recovered by seal_plan: transcript=71f94277 line=16631 utc=2026-11-13T03:57:22.446Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/mdg_build/work/data/r7/x; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - <<'PYEOF'
import json, collections
for d in ('r_119970', 'r_119971'):
    pref = collections.Counter(); scenes = set(); n = 0; first = None
    with open(d + '/clips_c.jsonl') as f:
        for line in f:
            r = json.loads(line); n += 1
            if first is None: first = r
            s = r.get('scene', ''); scenes.add(s); pref[s[:4]] += 1
    print(d, 'rows', n, 'distinct scenes', len(scenes), 'scene prefixes', dict(pref.most_common(6)))
    print('  first row: qid', first.get('qid'), '| path', str(first.get('path'))[:120], '| clip13 type', type(first.get('clip13')).__name__)
    print('  sample scenes', sorted(scenes)[:3], sorted(scenes)[-3:])
PYEOF