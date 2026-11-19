from common import *
seen=start('rebind.py')
from student_pilot.r2_exclusions import Exclusions,upstream
from student_pilot.r2_withheld import Withheld
from student_pilot.r2_scene_bindings import require_merged
from student_pilot.s1_exclusions import Exclusions as NativeExclusions
from student_pilot.row_removals import Removals
from student_pilot.r2_adapters import normalize
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import digest
build=load(ROOT/'out/BUILD.json');src=build['rows'];pin(src['path'],src['sha256'])
(ROOT/'u').mkdir(exist_ok=True)
base=load(ROUTE/'out/envelopes/camera_wording.json');stage_dependencies(base)
cov=load(ROUTE/'out/coverage/camera_wording_final.json');prior=load(ROUTE/'out/upstream/camera_wording.json')
assert cov['rows_sha256']==build['source']['sha256']
assert all(base['row_bindings'][r['qid']]==digest(r) for r in rows(SOURCE))
for p in prior['remove_files']:pin(p['path'],p['sha256'])
removals=Removals(prior['remove_files']);counts={};excluded=[];new_bindings={}
with scope(R.MAPS):
 rule=Exclusions(base['exclusions']);withheld=Withheld(base['withheld_rooms']);require_merged(base['dev_scene_exclusions'])
 merged=NativeExclusions(base['dev_scene_exclusions'],base['exclusions']['benchmark'])
 for raw in rows(src['path']):
  q=raw['qid'];row=normalize(raw);coverage=cov['rows'][q]
  reasons=rule.check(row,coverage)
  if withheld.touches(row,coverage):reasons.append('withheld_room')
  if merged.excluded(row):reasons.append('merged_dev_or_benchmark')
  hits=removals.match(raw)
  if hits:reasons.append('remove_files')
  kind=row['question_type'];c=counts.setdefault(kind,dict(seen=0,admitted=0,refused=0,reasons=Counter()));c['seen']+=1
  if reasons:
   c['refused']+=1;c['reasons'][','.join(reasons)]+=1;excluded.append(dict(qid=q,type=kind,reasons=reasons,remove_indices=hits))
  else:c['admitted']+=1
  new_bindings[q]=digest(raw)
assert new_bindings==build['row_bindings']
assert set(new_bindings)==set(cov['rows'])
capture(seen)
cp=write('out/coverage/camera_wording.json',dict(rows_sha256=src['sha256'],exclusions=base['exclusions'],rows=cov['rows'],source_coverage=pin(ROUTE/'out/coverage/camera_wording_final.json'),scope='Same independent coverage entries; only population hash is updated.'))
rp=write('out/upstream/camera_wording.json',dict(schema='fbp-exclusion-accounting-v1',exclusions=base['exclusions'],counts=counts,source_file=src,source_file_sha256=src['sha256'],coverage=cp,withheld_rooms=base['withheld_rooms'],dev_scene_exclusions=base['dev_scene_exclusions'],remove_files=prior['remove_files'],attests='All rows checked by unmodified Exclusions.check, Withheld.touches, merged-dev exclusion and Removals.match, as in route.py stage3. Counts attest exclusion eligibility before grammar; no exclusion was skipped.',prefiltered=base['prefiltered'],source_receipt=pin(ROUTE/'out/upstream/camera_wording.json')))
e={k:v for k,v in base.items() if k not in ['inputs','command','rows','row_bindings','scene_coverage','upstream_receipts','source_draft']}
e.update(rows=R.staged(src),row_bindings=new_bindings,scene_coverage=R.staged(cp),upstream_receipts=[R.staged(rp)],source_envelope=pin(ROUTE/'out/envelopes/camera_wording.json'),edit_manifest=pin(ROOT/'out/EDITS.json'))
with scope(R.MAPS):assert upstream(e['upstream_receipts'],e['exclusions'])
ep=write('out/envelopes/camera_wording.json',e)
write('out/REBIND.json',dict(envelope=ep,rows=src,coverage=cp,upstream=rp,counts=counts,excluded=excluded,paths=R.MAPS,coverage_entries_unchanged=len(new_bindings),bindings_recomputed=len(new_bindings)))
status(2,f'Envelope, coverage, upstream receipt and {len(new_bindings)} QID bindings are rebuilt using route helpers and native exclusion predicates. {len(excluded)} rows remain exclusion-ineligible; all rows remain in the delivered file.')
print(json.dumps(counts),flush=True)
