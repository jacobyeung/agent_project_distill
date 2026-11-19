"""Trace the accepted reader's fields to local, hashed routed-package records."""
from common import *
import re,importlib.util
ROOT=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
def main():
 def routed_digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
 ins={str(Path(__file__).resolve()):sha(__file__)};evidence={};missing=[]
 def source(rel):
  p=ROOT/rel;ins[str(p)]=sha(p);return p,read(p)
 def trace(p,field):return dict(file=str(p),sha256=ins[str(p)],field=field)
 ip,items=source('B/src/items/room134.json')
 meta='B5/ret/metadata/';journal=meta+'reads/0/metadata/journals/4/0/'
 ep,env=source(journal+'environment.json');mp,mapping=source(journal+'item_mapping.json')
 xp,export=source(meta+'EXPORT_PIN.json');rp,identity=source(meta+'reads/0/metadata/READ_IDENTITY.json')
 jp=ROOT/(journal+'items.jsonl');ins[str(jp)]=sha(jp)
 journal_rows=[json.loads(line) for line in jp.read_text().splitlines()]
 b=env['binding'];assert b['fixture'] is False and b['step']==export['step']==200 and identity['read']==0
 assert b['items_sha256']==ins[str(ip)]
 assert mapping['sha256']==b['mapping_sha256']==routed_digest(mapping['items'])
 manifest=W/'configs/R0DEV_ROOM_MANIFEST.json';ins[str(manifest)]=sha(manifest)
 direct=W/'evidence/direct_m200_room134.json';ins[str(direct)]=sha(direct);assert ins[str(direct)]==BASE
 old=read(direct);assert old['items_sha256']==ins[str(ip)] and ins[str(jp)] in old['journals'].values()
 # Reproduce all frozen baseline rows directly from the accepted journal.
 spec=importlib.util.spec_from_file_location('direct_extractor',W/'evidence/extract_direct.py')
 extractor=importlib.util.module_from_spec(spec);spec.loader.exec_module(extractor)
 ins[str(W/'evidence/extract_direct.py')]=sha(W/'evidence/extract_direct.py')
 item_by={r['id']:r for r in items['items']};map_by={r['id']:r for r in mapping['items']};jr={r['id']:r for r in journal_rows}
 assert len(jr)==len(journal_rows)==134
 for r in old['rows']:
  it=item_by[r['id']];j=jr[r['id']];match=re.search(r'</think>\s*(-?[0-9]+(?:\.[0-9]+)?)',j['output']['text'])
  pred=float(match.group(1)) if match else None
  assert j['complete'] is True and pred==r['direct'] and float(it['answer'])==r['gt']
  assert abs(extractor.mra(pred,r['gt'])-r['direct_mra'])<1e-9
  assert j['output']['scores']['answer']==r['direct_mra']
 frames={};frame_sources={}
 for r in read(manifest)['items']:
  ident=r['id'];it=item_by[ident];m=map_by[ident]
  assert it['r0_split']=='R0-dev' and it['native']==m['native']==jr[ident]['room_key']
  assert it['frame_indices']==it['source_frame_indices']==m['anchor_indices']==r['frame_indices']
  assert m['layout_count']==m['dense_count']==32
  assert m['task_sha256']==routed_digest(dict(it,answer=it['ground_truth']))
  assert m['frame_binding_sha256']==routed_digest(env['settings']['frames_json']['captures'][it['native']])
  frames[ident]=m['anchor_indices']
  frame_sources[ident]=[trace(ip,f'items[id={ident}].frame_indices'),trace(mp,f'items[id={ident}].anchor_indices'),trace(jp,f'id={ident}; complete=true')]
 assert len(frames)==98
 # export_sha256 is the reader's digest of sorted (relative path, file SHA256) pairs.
 # The receipt attests its recorded checkpoint identity; it does not claim a local weight rehash.
 checkpoint=b.get('export_sha256')
 if not isinstance(checkpoint,str) or not re.fullmatch('[0-9a-f]{64}',checkpoint):missing.append('environment.json.binding.export_sha256 (checkpoint_sha256)')
 for rel in ['B/src/h1eval/room134.py','B/src/h1eval/h10/parity_adapter.py','A/src/h1eval/items.py','A/src/h1eval/cli.py','A/src/h1eval/h10/launch.py','A/src/h1eval/h10/reserve_frames.py','A/src/tree/student_pilot/h1_r0.py']:
  p=ROOT/rel;ins[str(p)]=sha(p)
 assert ins[str(ROOT/'A/src/tree/student_pilot/h1_r0.py')]==b['r0_code_sha256']
 evidence.update(checkpoint_sha256=trace(ep,'binding.export_sha256'),step=[trace(ep,'binding.step'),trace(xp,'step')],read=trace(rp,'read'),journal=trace(ep,'location reads/0/metadata/journals/4/0/environment.json'),items_sha256=trace(ep,'binding.items_sha256'),journal_sha256=trace(jp,'sha256 of complete file'),baseline_sha256=dict(file=str(direct),sha256=BASE,field='sha256; all 134 answer/score rows replayed'))
 write(W/'configs/READER_RECEIPT.json',dict(status='MISSING' if missing else 'VERIFIED',missing=missing,baseline_sha256=BASE,step=200,read=0,journal='4/0',items_sha256=ins[str(ip)],journal_sha256=ins[str(jp)],checkpoint_sha256=checkpoint,
  checkpoint_identity_kind='reader-recorded export digest of sorted relative-file-path / file-sha256 pairs; checkpoint weights not rehashed locally',checkpoint_archive_sha256=export['archive_sha256'],checkpoint_archive_evidence=trace(xp,'archive_sha256'),frame_indices_by_item=frames,field_evidence=evidence,frame_evidence_by_item=frame_sources,command='bash scripts/cpu.sh scripts/reader_receipt.py'),ins)
 status('READER_RECEIPT.json is '+('MISSING: '+', '.join(missing) if missing else 'VERIFIED: all 98 frame lists match the reader mapping and kit manifest; all 134 direct answers/scores replay; checkpoint identity is backed by the accepted journal environment.')+' No GPU launch is authorized.')
 print('reader receipt',len(frames),'rooms', 'MISSING' if missing else 'VERIFIED')
if __name__=='__main__':main()
