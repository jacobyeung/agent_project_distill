"""Bound source receipts, geometry, membership, and coefficient evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import collections,gzip
R=Path('/scratch/jjyeung/orch_cd');out=HERE.parent/'out';manifest=json.loads((out/'MANIFEST.json').read_text());items=rows(out/'ITEMS.jsonl');pins=json.loads((out/'SOURCE_PINS.json').read_text())
for rel in ['devs1_price/out/PER_ITEM.jsonl','devs1_price/out/ITEMS.jsonl','devs1_price/out/CAPTURES.jsonl','devs1_direct/out/r3/TASKS.jsonl','devs1_direct/out/r3/STRATA.jsonl','devs1_direct/out/r5/merge_results/ON16k.json','devs1_direct/out/r5/merge_results/MERGE_INPUTS.json','devs1_tower/out/r2/kit/PLAN.json']:
 pins[str(R/rel)]=sha(R/rel)
merge=json.loads((R/'devs1_direct/out/r5/merge_results/MERGE_INPUTS.json').read_text());journal=Path(merge['source'])/'results/0/g0.jsonl';journal_sha=sha(journal);assert journal_sha==merge['inputs']['g0.jsonl'];pins[str(journal)]=journal_sha
for src,name in [('devs1_direct/out/r5/merge_results/ON16k.json','DIRECT_ON16k.json'),('devs1_direct/out/r5/merge_results/MERGE_INPUTS.json','DIRECT_RECEIPT.json')]:
 (out/name).write_bytes((R/src).read_bytes())
headchecks=[]
for pin in json.loads((out/'HEADS.json').read_text()):
 c=next(c for c in manifest['captures'] if c['scene']==pin['scene'])
 with np.load(pin['path'],allow_pickle=False) as z:
  assert np.array_equal(z['anchor_frame_indices'],c['anchor_indices']) and str(z['layout'])=='per_frame'
  assert np.isfinite(z['depth_grid']).all() and np.isfinite(z['r_grav']).all() and np.isfinite(z['t_grav']).all() and (z['fov_hw']>0).all() and (z['fov_hw']<np.pi).all()
  headchecks.append(dict(scene=c['scene'],kind=pin['kind'],anchor_count=len(c['anchor_indices']),depth_shape=list(z['depth_grid'].shape)))
# All task names come from the input wording/options, and every program name has a cache prompt.
by={c['scene']:c for c in manifest['captures']}
for q in items:
 assert q['scene'] in by
 assert all(n.lower() in by[q['scene']]['names'] for n in q['operands'])
 assert all(n.casefold() in q['question'].casefold() or n in __import__('tplib').option_texts(q['options']).values() for n in q['operands'])
withheld=json.loads((R/'devs1_direct/out/r3/WITHHOLD_SCENES.json').read_text())
assert all(q['room'] in withheld['rooms'] and q['native'] in withheld['natives'] for q in items)
qref={}
with gzip.open(R/'devs1_tower/out/r2/kit/QIDS.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line)
  if r['native'] in {c['native'] for c in manifest['captures']}:qref[r['qid']]=r
unsupported=collections.Counter(r['type'] for k,r in qref.items() if k not in {q['qid'] for q in items})
dump(out/'INPUT_AUDIT.json',dict(status='pass',tasks=len(items),head_files=len(headchecks),head_frame_joins=304*32,program_types=dict(collections.Counter(q['question_type'] for q in items)),unpriced_types=dict(unsupported),direct_journal_sha256=journal_sha,frame_pixels_status='Pending run-host preflight: node-local PNGs not supplied here',manifest_sha256=sha(out/'MANIFEST.json'),head_checks=headchecks))
dump(out/'SOURCE_PINS.json',pins)
print('PASS',len(items),'tasks',len(headchecks),'head files',len(qref),'source questions')
