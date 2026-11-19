"""Extract registered training records without decoding held-out records."""
from common import *
import re
from collections import Counter

def main():
 pins()
 source=Path('/scratch/jjyeung/orch_n30/sb_kobj2/inputs/local/K1_MANIFEST.json')
 blob=read(source)
 blocks=re.findall(rb'^    \{\n.*?^    \}',blob,re.M|re.S)
 captures=[json.loads(b) for b in blocks if re.search(rb'^      "k1_split": "train",?$',b,re.M)]
 allowed=set(read(ROOT/'inputs/rowsets/K1_CAPTURES_TRAIN_239.txt').decode().splitlines())
 assert allowed<={c['canonical'] for c in captures}
 captures=[c for c in captures if c['canonical'] in allowed]
 wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines())
 tables=set(read(ROOT/'inputs/rowsets/K1_TRAIN_TABLES_883.txt').decode().splitlines())
 assert tables<=wanted
 selected=[]
 for c in captures:
  rr=[r for r in c['rows'] if r['id'] in wanted]
  if rr:
   # Preserve existing registrations; do not generate rows or frame mappings.
   selected.append(dict(c,rows=rr))
 assert {r['id'] for c in selected for r in c['rows']}==wanted
 write(ROOT/'inputs/local/K1_MANIFEST.json',dict(schema='registered-K1-train-only',captures=selected,heldout_records_decoded=0))
 counts={}
 for ds in ['all','arkitscenes','scannet','scannetpp']:
  cs=[c for c in selected if ds=='all' or c['canonical'].startswith(ds+'/')]
  rr=[(c,r) for c in cs for r in c['rows']]
  counts[ds]=dict(captures=len(cs),rooms=len({c['room'] for c in cs}),rows=len(rr),table_rows=sum(r['id'] in tables for c,r in rr),capture_name_jobs=sum(len({str(n).lower().strip() for r in c['rows'] for n in r['operands']}) for c in cs))
 write(ROOT/'out/TRAIN_CENSUS.json',dict(status='COMPLETE',selection_split='K1-train',counts=counts,heldout_records_decoded=0,mixed_container_note='Container bytes hashed; only blocks with explicit k1_split=train JSON-decoded. No held-out caches, labels, frames, or outcomes opened.'))
 from k1_track import jobs
 work=jobs();by={}
 for scene,names,split in work:
  by.setdefault(scene['capture'],dict(scene=scene,names=[]))['names']+=names
 # Two predefined captures from the kit CPU checks; use all their operand names.
 names=['arkitscenes/41125837','scannetpp/067e2e4e61']
 assert all(n in by for n in names)
 write(ROOT/'out/CPU_TRACK_PLAN.json',dict(status='FIXED_BEFORE_INFERENCE',pilot=[by[n] for n in names],pilot_rule='The two captures used by the inherited CPU dry run, all registered operand names, all 32 anchors.',subset_rule='Only if a successful pilot projects above 8 CPU-hours: stratify by dataset; sort captures within each dataset by SHA256 of canonical ID; round-robin arkitscenes, scannet, scannetpp; admit complete captures with all operand names while the conservative projected process CPU total stays at most 6 hours. Require all three datasets. No successful pilot means no subset and no extrapolated CPU number.',cpu_hours_definition='Summed user+system process CPU time, not wall time.',maximum_threads=8,nice=10))
 original=Path('/scratch/jjyeung/orch_n30/sb_kobj2/out/TRACK_SELECTION.json')
 selection=js(original);write(ROOT/'out/TRACK_SELECTION.json',selection)
 status('The kit is copied with train-only data. The registered rowsets and 32-anchor jobs are verified. The two-capture CPU pilot and a conditional three-dataset subset rule are fixed before inference. Held-out manifest blocks were not decoded and no held-out outcomes were opened.')
 print(json.dumps(counts))

if __name__=='__main__':main()
