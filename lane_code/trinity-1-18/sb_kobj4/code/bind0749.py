"""Snapshot only registered train predictions and record missing native exports."""
from common import *
import ast,gzip
BOX=Path('/scratch/jjyeung/orch_n30/sb_kbox4');B=BOX/'out/box_ladder'
REQUIRED=['count_objects','object_source','price_k1_tracks','stage1_replay']

def main():
 pins()
 for p in (ROOT/'inputs/ruling0749').glob('*.md'):sha(p)
 accepted=read(ROOT/'inputs/ruling0749/KIT_SPEC_object_route_r0dev_v2.md')
 assert hashlib.sha256(accepted).hexdigest()=='640e8deb8fe7d661abbeb3bb0d345aeb2b6eda4f50af346f0f16b0cf4788cce3'
 (ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md').write_bytes(accepted)
 sha(ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md')
 manifest=js(ROOT/'inputs/local/K1_MANIFEST.json');wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines())
 assert all(c['k1_split']=='train' for c in manifest['captures'])
 folder=ROOT/'inputs/kbox4';folder.mkdir(exist_ok=True)
 receipts={}
 for name in ['FREEZE.json','REFERENCE_REBUILD.json','A0_REPLAY.json','DECISION.json']:
  p=B/name
  if not p.exists():continue
  data=read(p);q=folder/name;q.write_bytes(data);receipts[name]=dict(path=str(q.relative_to(ROOT)),sha256=sha(q),source_path=str(p),source_sha256=PINS[str(p)])
 reference=js(folder/'REFERENCE_REBUILD.json');assert reference['status']=='PASS'
 reference_captures={c['capture']:c for c in reference['captures']}
 exported={}
 # Bounded top-level source audit; never import sibling code that writes there.
 for p in sorted(BOX.glob('*.py')):
  names={n.name for n in ast.parse(read(p)).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  for name in names & set(REQUIRED):exported.setdefault(name,[]).append(dict(path=str(p),sha256=PINS[str(p)]))
 entries={};seen=set()
 for c in manifest['captures']:
  ids={r['id'] for r in c['rows']} & wanted
  if not ids:continue
  key=c['canonical'].replace('/','__');source=B/'base'/(key+'.json');raw=read(source);data=json.loads(raw)
  assert data['capture']==c['canonical'] and data['phase']=='base'
  a0=[r for r in data['items'] if r['arm']=='A0_deployed'];assert {r['row_id'] for r in a0}==ids
  assert all(r['split']=='train' and r['row_id'] in ids for r in data['items'])
  # Preserve every upstream hash without opening any upstream data.
  data['input_sha256'][str(source)]=PINS[str(source)]
  q=folder/(key+'.json.gz');q.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))
  table=B/'serving_tables'/(key+'.json.gz')
  rebuilt=False;table_sha=None
  if table.exists():
   table_raw=read(table);table_sha=PINS[str(table)]
   t=json.loads(gzip.decompress(table_raw))
   assert t['capture']==c['canonical'] and t['split']=='train' and t['room']==c['room']
   assert reference_captures[c['canonical']]['sha256']==table_sha
   # Empty candidate tables are valid rebuilt tables, not missing captures.
   rebuilt=True
  entries[c['canonical']]=dict(snapshot_path=str(q.relative_to(ROOT)),snapshot_sha256=sha(q),source_path=str(source),source_sha256=PINS[str(source)],rebuilt_table=rebuilt,table_path=str(table),table_sha256=table_sha,rows=len(ids))
  seen|=ids
 assert seen==wanted
 write(ROOT/'inputs/KBOX_SNAPSHOT.json',dict(status='BOUND_TRAIN_SNAPSHOT',selection_split='K1-train',captures=entries,receipts=receipts,replay=receipts['A0_REPLAY.json']))
 write(ROOT/'config/KBOX_RULES_HOOK.json',dict(status='BOUND_TRAIN_SNAPSHOT',module_path=str(ROOT/'code/kbox_snapshot.py'),module_sha256=sha(ROOT/'code/kbox_snapshot.py'),receipt_path=str(ROOT/'inputs/KBOX_SNAPSHOT.json'),receipt_sha256=sha(ROOT/'inputs/KBOX_SNAPSHOT.json'),required_interface=REQUIRED,native_exports=exported,missing_native_exports=sorted(set(REQUIRED)-set(exported)),native_expected_module=str(BOX/'box_math.py'),live_binding_status='MISSING',reason='Serialized training outputs are bound; native live exports and final selected construction are required for live pricing'))
 write(ROOT/'inputs/PACKAGE_D_BINDING.json',dict(status='MISSING',lane='cont_ops18',package='D',expected_location='/scratch/jjyeung/orch_n30/cont_ops*/ (cont_ops18 package-D return manifest)',search_command='ls -d /scratch/jjyeung/orch_n30/cont_ops*',search_result='No such file or directory',returns=[],slots=[dict(step=544,job=172957,status='MISSING',path=None,sha256=None,original_wording_twins=290,reworded_items=290),dict(step=200,status='MISSING',path=None,sha256=None,original_wording_twins=290,reworded_items=290)],comparison_allowed=False,reconstruction_under_S4=False))
 status('Stage 2: The accepted spec and 0749Z documents are pinned. Registered sb_kbox4 training predictions and serving-reference replay are snapshotted with hashes. The hook exposes the saved training outputs; native live exports are recorded separately and cannot be substituted. Package-D remains MISSING. No evaluation split was opened.')
 print(json.dumps(dict(captures=len(entries),rows=len(seen),retained_A0_rows=sum(e['rows'] for e in entries.values() if not e['rebuilt_table']),native_exports=exported)))

if __name__=='__main__':main()
