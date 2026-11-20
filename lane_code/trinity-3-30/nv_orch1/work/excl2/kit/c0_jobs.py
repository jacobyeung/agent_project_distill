"""nvkey1 C0: fat presence-and-point census tasks for the dev-S1 routed-distance captures (one call = every asked name x the 32 read frames).
usage: c0_jobs.py OUT.jsonl MODEL EFFORT [max_side] ; C1_EXTRA env adds request fields (e.g. Claude thinking)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
from c1_jobs import PROMPT
out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; side = int(sys.argv[4]) if len(sys.argv) > 4 else 640
effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}'))
man = json.load(open(K + '/c0/C0_MANIFEST.json')); tag = model.split('/')[-1]; n = 0
with open(out, 'a') as f:
    for sc, m in man.items():
        if m['frames_present'] != 32: print('skip incomplete', sc); continue
        kinds = m['names']; content = [{'text': PROMPT.format(n=32, kinds=json.dumps(kinds), k0=kinds[0])}]
        for i, p in enumerate(m['frames']): content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
        f.write(json.dumps({'id': '%s_%s_f32_s%d' % (sc.replace('/', '__'), tag, side), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                            'content': content, 'meta': {'scene': sc, 'n': 32, 'side': side, 'kinds': kinds}}) + '\n'); n += 1
print('wrote', n, 'tasks to', out)
