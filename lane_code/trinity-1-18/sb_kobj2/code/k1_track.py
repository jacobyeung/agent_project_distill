"""Pinned K1 tracker jobs and paired source choice. Held-out rows cannot enter."""
from common import *
from route_stats import paired

def jobs():
 wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines())
 manifest=js(ROOT/'inputs/local/K1_MANIFEST.json');out=[];found=set();captures=set()
 for c in manifest['captures']:
  if c['k1_split']!='train':continue
  rr=[r for r in c['rows'] if r['id'] in wanted]
  if not rr:continue
  found.update(r['id'] for r in rr);captures.add(c['canonical'])
  anchors=c['anchor_indices'];frames=[{k:f[k] for k in ('index','path','sha256')} for f in c['dense_frames'] if f['index'] in anchors]
  assert [f['index'] for f in frames]==anchors and anchors==sorted(anchors) and len(anchors)==32
  scene=dict(scene=c['canonical'].replace('/','__'),capture=c['canonical'],room=c['room'],dataset=c['canonical'].split('/')[0],split='K1-train',frames=frames,f32=anchors,anchor_slots=list(range(32)))
  for name in sorted({str(n).lower().strip() for r in rr for n in r['operands']}):out.append((scene,[name],'K1-train'))
 if found!=wanted:raise Missing('K1 manifest lacks registered rows: '+str(sorted(wanted-found)))
 assert len(captures)==209,(len(captures),'expected 209 K1 train captures')
 return out

def choose(evidence_path):
 d=js(evidence_path)
 assert d['selection_split']=='K1-train'
 wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines())
 assert d['rowset_sha256']==sha(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt')
 comparisons={}
 for rule in ('today','frozen'):
  rr=d['paired_rows'][rule];assert {r['row_id'] for r in rr}==wanted and len(rr)==len(wanted)
  assert all(r['split']=='K1-train' for r in rr)
  comparisons[rule]=paired([dict(qid=r['row_id'],room=r['room'],head_score=r['track_score'],direct_score=r['linker_score'],refusal_code=None) for r in rr])
 pairs=d['first_seen_pairs'];assert pairs and all(r['split']=='K1-train' for r in pairs)
 rate=sum(bool(r['correct']) for r in pairs)/len(pairs)
 write(ROOT/'out/object_route/K1_TRACK_CHOICE.json',dict(status='COMPLETE',selection_split='K1-train',box_source='track' if comparisons['frozen']['ci95'][0]>0 else 'linker',comparisons=comparisons,first_seen_pair_rates={'track':rate},n_track=d['n_track'],counts_decide=False))

def price():
 from box_hook import load
 from evaluate import read_pass
 hook,gate=load(True)
 if not hasattr(hook,'price_k1_tracks'):raise Missing('KBOX_RULES_HOOK.price_k1_tracks: sibling deployed geometry and registered GT pairs')
 wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines())
 manifest=js(ROOT/'inputs/local/K1_MANIFEST.json');paired_rows={'today':[],'frozen':[]};pairs=[];counts=[]
 for c in manifest['captures']:
  if c['k1_split']!='train':continue
  rr=[r for r in c['rows'] if r['id'] in wanted]
  if not rr:continue
  sid=c['canonical'].replace('/','__');names=sorted({str(n).lower().strip() for r in rr for n in r['operands']})
  tracks={n:read_pass('k1_track',sid+'/'+digest(n)[:16],'TRACKS.json.gz')['tracks'] for n in names}
  # The sibling owns deployed geometry, frozen A4 and first-seen pair registration.
  result=hook.price_k1_tracks(c,rr,tracks,gate['rule'])
  for rule in paired_rows:paired_rows[rule]+=result['paired_rows'][rule]
  pairs+=result['first_seen_pairs'];counts+=result['n_track']
 evidence=ROOT/'inputs/K1_TRACK_EVIDENCE.json'
 write(evidence,dict(selection_split='K1-train',rowset_sha256=sha(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt'),paired_rows=paired_rows,first_seen_pairs=pairs,n_track=counts))
 choose(evidence)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--evidence');a=p.parse_args()
 if a.evidence:choose(a.evidence)
 else:price()
