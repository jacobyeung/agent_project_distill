"""Reviewer's check of what the run-bound readout training_scenes list matches."""
import gzip, json
from pathlib import Path
ORCH = Path('/scratch/jjyeung/orch_n30'); AWS = ORCH / 'sb_evidence/aws_sources'; HERE = Path(__file__).resolve().parent
P = 'ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__'
NAMES = {'pointing': P + 'pointing__rows.scenes.jsonl.gz', 'routing': P + 'routing__rows.scenes.jsonl.gz',
         'vqa': P + 'vqa__rows.scenes.jsonl.gz', 'a2v3': 'ap__f02f16ad__s__a2v3__rows.scenes.jsonl.gz',
         'a3v2': 'ap__f02f16ad__s__a3v2__rows.scenes.jsonl.gz', 'r16': 'ap__5e1d07a4__f__h__r16__rows.scenes.jsonl.gz'}
IDX = {'pointing': 'pointing_scene_indices.json', 'routing': 'routing_scene_indices.json', 'vqa': 'vqa_scene_indices.json'}
def rows(n):
    with gzip.open(AWS / n, 'rt') as f: return [json.loads(l) for l in f]
S = {k: rows(v) for k, v in NAMES.items()}
key = lambda r: (r['dataset'], r['scene'])
raw = {k: {key(r) for r in v} for k, v in S.items()}
adm = set()
for k, f in IDX.items():
    for i in json.load(open(AWS / (P + 'prepared__' + f))): adm.add(key(S[k][i]))
for src, i in json.load(open(AWS / (P + 'prepared__pose_scene_order.json'))):
    adm.add(key(S['a2v3' if src == 0 else 'a3v2'][i]))
fu = set()
with gzip.open(ORCH / 'sb_framepool/work/frame_map.jsonl.gz', 'rt') as f:
    for l in f: r = json.loads(l); fu.add((r['d'], r['s']))
tr = {tuple(x) for x in json.load(open(AWS / 'ap__e84d901c__z__eb035f92.json'))['scenes']}
rawu = set().union(*raw.values()); raw5 = set().union(*(raw[k] for k in raw if k != 'r16'))
out = dict(training_scenes=len(tr), admitted_union=len(adm), raw_union=len(rawu), raw_union_no_r16=len(raw5), frame_universe=len(fu),
           tr_minus_frame_universe=len(tr - fu), tr_minus_raw=len(tr - rawu), tr_inter_admitted=len(tr & adm),
           admitted_minus_tr=len(adm - tr), tr_minus_admitted=len(tr - adm),
           tr_minus_admitted_in_raw={k: len((tr - adm) & raw[k]) for k in raw})
(HERE / 'rev_readout.json').write_text(json.dumps(out, indent=1) + '\n'); print(out)
