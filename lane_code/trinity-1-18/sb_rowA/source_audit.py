"""Read-only, local source census. No training admission is inferred from metadata."""
import hashlib,json,sqlite3,subprocess
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
W19=TREE.parents[1]
TYPES=('camera_displacement','camera_rotation','camera_movement_direction')
INPUTS={}
def pin(p):
 p=Path(p).resolve()
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 INPUTS[str(p)]=h
 return {'path':str(p),'sha256':h}
def load(p):pin(p);return json.loads(Path(p).read_text())
def main():
 pin(__file__)
 seal=load(W19/'out/TREE_SEAL.json')
 for rel in ['student_pilot/ground_rows.py','student_pilot/r1_rooms.py','student_pilot/r1_routing.py','student_pilot/s1_routing.py','generator/derivgen_v7/derivgen/camera_rows.py','generator/derivgen_v7/derivgen/ground_v312_quality.py']:
  assert pin(TREE/rel)['sha256']==seal['files'][rel]
 cfg=load(W19/'work/build19/inputs/config.json')
 for p in cfg['r1_training']['room_authority'].values():assert pin(p['path'])['sha256']==p['sha256']
 comp=load(W19/'work/build19/inputs/component_rows.json')
 for p in comp['inputs']:assert pin(p['path'])['sha256']==p['sha256']
 v7=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
 idx=load(v7/'FAMILY_INDEX_RANGES.json');load(v7/'BUILD_MANIFEST.json');load(v7/'COUNTS_V7.json');load(v7/'EXCLUSIONS.json')
 dbpin=pin(v7/'vqa/rows.sqlite')
 assert dbpin['sha256']=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
 conn=sqlite3.connect('file:'+dbpin['path']+'?mode=ro&immutable=1',uri=True)
 counts=Counter();total=0
 for (raw,) in conn.execute('SELECT row FROM rows'):
  r=json.loads(raw);counts[r.get('question_type',r.get('type','MISSING'))]+=1;total+=1
 conn.close();assert total==204413
 assert all(counts[t]==0 and t not in idx['families'] for t in TYPES)
 r2=Path('/scratch/jjyeung/n30_mirror/rows_r2')
 files=subprocess.check_output(['rg','--files',str(r2)],text=True).splitlines()
 rowfiles=[p for p in files if p.endswith('.jsonl')]
 r2counts={}
 for p in rowfiles:
  pin(p);c=Counter();n=0
  with open(p) as f:
   for line in f:
    if line.strip():
     r=json.loads(line);c[r.get('question_type',r.get('type','MISSING'))]+=1;n+=1
  r2counts[p]={'rows':n,'camera_counts':{t:c[t] for t in TYPES}}
 assert all(not any(x['camera_counts'].values()) for x in r2counts.values())
 base=W19/'fixtures/work/kit07ca49df_meta/m'
 receipt_path=base/'runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/receipt.json'
 receipt=load(receipt_path)
 material=load(receipt_path.parent/'materialization.json')
 selection=load(base/'k/pool_selection.json')
 assert pin(base/'k/pool_selection.json')['sha256']==cfg['s1_routing']['selection']['sha256']
 missing=[]
 for label,p in [('admitted_routing_database',receipt['database']),('legacy_r16_receipt',material['legacy'])]:
  assert not Path(p['path']).exists()
  missing.append(dict(name=label,**p,status='MISSING'))
 # A filename inventory can find relocated databases, but cannot authenticate absent payloads.
 inv=subprocess.check_output(['rg','--files','/scratch/jjyeung/n30_mirror',str(W19/'fixtures')],text=True).splitlines()
 localdb=[p for p in inv if p.endswith('.sqlite')]
 (OUT/'routing_database_inventory.txt').write_text('\n'.join(localdb)+'\n')
 # Pin known exclusion inputs even though no source rows are available to admit.
 dev=base/'k/dev_scene_exclusions.json';assert pin(dev)['sha256'].startswith('969cdb56')
 report=dict(status='MISSING',tree=str(TREE),tree_sha256=seal['tree_sha256'],
  store_v7={'database':dbpin,'rows':total,'camera_counts':{t:counts[t] for t in TYPES},'family_index_agrees':True},
  rows_r2=r2counts,metadata_only_routing_counts={t:receipt['types'][t+':route'] for t in TYPES},
  metadata_only_legacy_counts={t:material['legacy_compatibility'][t]['source_rows'] for t in TYPES},
  routing_receipt=pin(receipt_path),missing=missing,
  caveat='Receipt counts describe its existing routed population; post-N room-filter counts and row contents cannot be verified without the bound database.',
  input_sha256=INPUTS)
 (OUT/'SOURCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
 (ROOT/'STATUS.md').write_text('Source audit: store v7 has 204,413 rows and zero rows in each requested camera-motion family. The rows_r2 JSONL census also has zero camera-motion rows. N’s separate routing database and its legacy r16 receipt are MISSING at their pinned paths. Training-row generation is blocked; the held-out item set and independent wording inventory can be built.\n')
 print(json.dumps({k:report[k] for k in ['status','metadata_only_routing_counts','missing']}))
if __name__=='__main__':main()
