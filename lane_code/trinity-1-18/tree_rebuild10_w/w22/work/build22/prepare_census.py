from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
s=(L/'work/build21/census21.py').read_text()
s=s.replace("B=L/'work/build21'","B=L/'work/build22'")
s=s.replace("Rows(dict(streams={'vqa':v},r1_training=value)","Rows(dict(streams={'vqa':v},r1_training=value,remove_files=cfg['remove_files'])")
s=s.replace("Rows(dict(streams={},r1_training=value,extent_receipt=cfg['extent_receipt'])", "Rows(dict(streams={},r1_training=value,extent_receipt=cfg['extent_receipt'],remove_files=cfg['remove_files'])")
s=s.replace('from tests.test_r2_build9_recovery import envelope', '''from tests.test_r2_build9_recovery import envelope as original_envelope
def envelope(folder,rows,stream,family):
 if family!='camera_wording':return original_envelope(folder,rows,stream,family)
 from student_pilot.r2_contract import CONTRACT
 from student_pilot.r2_grammar import SHARED_SHA256
 from tests.test_r2_data_path import RECORDS,SOURCES
 path=folder/'rows.jsonl';path.write_text(''.join(json.dumps(r)+'\\n' for r in rows))
 pins={role:file_pin(RECORDS/name) for role,name in SOURCES.items()}
 write(folder/'coverage.json',dict(exclusions=pins,rows_sha256=file_pin(path)['sha256'],rows={
  r['qid']:dict(status='known',names=[r['dataset']+'/'+r['scene'],r['provenance']['canonical']]) for r in rows}))
 result=dict(schema='r2-family-manifest-v1',family=family,stream=stream,count=len(rows),trace_contract=CONTRACT,
  validator_sha256=SHARED_SHA256,rows=file_pin(path),row_bindings={r['qid']:digest(r) for r in rows},
  scene_coverage=file_pin(folder/'coverage.json'),exclusions=pins,upstream_receipts=[],
  routing_policy='both-path-20261116',artifact_heads=['pose','depth'])
 write(folder/'MANIFEST.json',result);return folder/'MANIFEST.json' ''')
s=s.replace("audit,_=R.census(cfg);", "audit,_=R.census(cfg);")
# Count authenticated twins with the same native reader and preparation predicates.
s=s.replace("reader.close();assert found==union",'''if value.get('direction_twins'):
 from student_pilot.r1_direction_twins import Binding
 twins=Binding(cfg)
 for row in twins.rows():
  guard.check(row);cell=family(row,'vqa');why=filters.reason(row,'vqa')
  if why:refused[why]+=1
  else:
   from student_pilot.r1_training import row_check
   row_check(row,'vqa');admit(row,cell);counts[cell]+=1
reader.close();assert found==union''')
s=s.replace("for name in ('recovery','absolute_distance','units'):eligible[name]=slice_counts[name]['counts'].get('eligible',0)","for name in ('recovery','absolute_distance','units','camera_wording'):eligible[name]=slice_counts[name]['counts'].get('eligible',0)")
s=s.replace("mp=envelope(chunk,normalized,'routing',kind);", "mp=envelope(chunk,normalized,'routing',kind);")
(D/'census.py').write_text(s)
