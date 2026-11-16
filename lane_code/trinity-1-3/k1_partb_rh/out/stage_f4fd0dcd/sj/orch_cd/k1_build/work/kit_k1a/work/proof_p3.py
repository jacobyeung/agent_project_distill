import os,sys,json
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
sys.path.insert(0,str(Path(__file__).parent))
import backend,gate,prooflib,k1_pipeline
def proof():
 root=Path('/scratch/jjyeung/mask_recall_run/results/dense_aliases')
 m=json.loads((root/'MANIFEST.json').read_text())
 p=backend.pricing(fixture=True)
 items=p.rows(gate.ROOT/'mask_recall/out/kit/out/ITEMS.jsonl')
 refs={r['qid']:r for r in p.rows(root/'priced/PER_ITEM.jsonl') if (r['arm'],r['source'],r['policy'])==('predicted','g3t','frozen')}
 exports=gate.ROOT/'devs1_price/work/exports/devs1_r2';results=[];inputs={}
 for ds in ['scannet','scannetppv2','arkitscenes']:
  options=[]
  for c in m['captures']:
   qs=[q for q in items if q['scene']==c['scene'] and q['question_type'] in ('object_abs_distance','room_size_estimation')]
   if c['scene'].startswith(ds+'/') and len(qs)>=7:options.append((c,qs))
  c,qs=options[0];qs=qs[:8];sid=c['scene'].replace('/','__');rp=root/'candidates'/(sid+'.npz');hp=exports/('heads_'+c['group']+'_vcd')/(sid+'.npz')
  raw=p.load_cache(rp)
  inputs[str(rp)]=gate.sha(rp);inputs[str(hp)]=gate.sha(hp)
  print('Replay',c['scene'],len(qs),flush=True)
  for r in k1_pipeline.price_reference(c,raw,hp,exports,qs,fixture=True):
   expected=refs[r['qid']];same=r['pred']==expected['pred'] and r['error']==expected['error']
   results.append(dict(**r,scene=c['scene'],expected_pred=expected['pred'],expected_error=expected['error'],exact=same))
 assert len(results)>=20 and all(r['exact'] for r in results),results
 return dict(items=len(results),datasets=3,fixture_only=True,rows=results,input_sha256=inputs,reference=str(root/'priced/PER_ITEM.jsonl'))
if __name__=='__main__':raise SystemExit(not prooflib.run('P3',proof))
