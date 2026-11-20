"""nv_orch1 V4 flags (RULING 0436Z: FLAGS ONLY; spec O7 form = nvkey2's V1 judge form (c), v1c_jobs.PROMPT 224371a3 verbatim, 24 claims per call,
ring on the 640-px frame plus the v1c 256-px close-up for point rows). Rows: N's 18,116 admitted pointing rows (store c09bb5ca rows whose scene passes
excl.py; exact match with AUDIT_POINTING_K1 scene_ok), visible rows only at 1% of the frame or more, every null row at class level (no floor).
One clip per call, rows shuffled per clip (seed 'v4 ' + clip). Both families judge every row; a row is flagged only when both flag it.
usage: NVK=work/v6f python build_v4.py OUT.jsonl MODEL EFFORT"""
import gzip, json, sys, random, collections, hashlib
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
sys.path.insert(0, W + 'v6f/kit'); import excl
src = open(W + 'v1c/v1c_jobs.py').read(); ns = {}
exec(src[src.index('PROMPT = ('):src.index('ALLOW = set(')], ns); PROMPT = ns['PROMPT']; PSHA = hashlib.sha256(PROMPT.encode()).hexdigest()
assert PSHA.startswith('224371a3'), PSHA
out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; effort = None if effort == 'none' else effort; mtag = model.split('/')[-1]
rows = [json.loads(l) for l in gzip.open(W + 'pointing_meta.jsonl.gz', 'rt')]
adm = [r for r in rows if not excl.reasons(r['scene'])]; assert len(adm) == 18116, len(adm)
use = [r for r in adm if r['kind'] == 'gt_absent' or (r['area'] or 0) >= 0.01]
by = collections.defaultdict(list)
for r in use: by[r['scene']].append(r)
n = 0
with open(out, 'w') as f:
    for cn in sorted(by):
        rs = by[cn][:]; random.Random('v4 ' + cn).shuffle(rs); room = excl.room(cn)
        for gi in range(0, len(rs), 24):
            part = rs[gi:gi + 24]; content = [{'text': PROMPT.format(n=len(part))}]
            for r in part:
                rid = 'r%d' % r['i']; img = 'tar:' + r['rgb']
                if r['kind'] == 'gt_absent': content += [{'text': 'Row %s (absent row): kind = "%s"' % (rid, r['label'])}, {'image': img, 'max_side': 640}]
                else: content += [{'text': 'Row %s (point row): kind = "%s"' % (rid, r['label'])}, {'image': img, 'max_side': 640, 'mark': r['uv']},
                                  {'text': 'Row %s close-up' % rid}, {'image': img, 'max_side': 256, 'crop_v1c': r['uv']}]
            f.write(json.dumps({'id': 'v4_%s_%02d_%s' % (hashlib.sha256(cn.encode()).hexdigest()[:10], gi // 24, mtag[:6]), 'model': model, 'effort': effort, 'max_tokens': 16384,
                                'content': content, 'meta': {'tag': 'train', 'scenes_h': [hashlib.sha256(cn.encode()).hexdigest(), hashlib.sha256(room.encode()).hexdigest()],
                                'rows': ['r%d' % r['i'] for r in part], 'form': 'v1c', 'prompt_sha256': PSHA, 'flags_only': True}}) + '\n'); n += 1
print(mtag, 'admitted', len(adm), 'judged rows', len(use), collections.Counter(r['kind'] for r in use), 'clips', len(by), 'tasks', n)
