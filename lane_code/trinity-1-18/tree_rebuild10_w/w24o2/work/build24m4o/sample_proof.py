import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import gzip,copy,importlib.util
from collections import Counter
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
nd=mod('nd_proof',L/'out/rcj/nd.py');rdmod=mod('rd_proof',L/'work/build24m4n/rdiff.py')
rd=json.loads(gzip.decompress((E/'rd0/rdiff.json.gz').read_bytes()))
bykey={tuple(r['key']):r for r in rd['N']}
reference=z.load(E/'p_sample.json')
proof=[];fields=Counter();top=Counter();nbytes=0;sample_rows=[];missing=[]
for s in reference['rows']:
 row=json.loads(s['row']);nr=bykey.get(nd.key(row))
 if nr is None:
  missing.append(dict(**{'class':s['class']},position=s['position'],P_i=s['i'],key=nd.key(row)))
  continue
 new=copy.deepcopy(row)
 if row.get('s1_source'):
  r=row['routing'];si=row['student_input']
  added=dict(source_qid=row['s1_source']['provenance'].get('source_qid',r['qid']),candidate_id=r['candidate_id'],question=si['question'],question_type=r['question_type'],answer=r['answer'],gt_answer=r['gt_answer'],ground_record=r['ground_record'],provenance=row['s1_source']['provenance'],tool_output_spans=r['tool_output_spans'])
  new={}
  for k,v in row.items():
   if k=='routing':new.update(copy.deepcopy(added))
   new[k]=copy.deepcopy(v)
  for p in [new['s1_source']['source'],*new['s1_source']['frame_binding']['authority'].values()]:p['path']='/tmp/q_22c714e1/p/q/u/'+p['sha256']
  new['s1_source']['frame_binding']['fps_source']='source_row' if row['s1_source']['name']=='U_Faithful' else 'native_scene_metadata'
 raw=json.dumps(new)
 h=hashlib.sha256(rdmod.packed((nr['i'],raw,s['target']))).hexdigest()
 proven=h==nr['content_sha256']
 entry=dict(P_i=s['i'],N_i=nr['i'],key=nd.key(row),source=nd.key(row)[3],proven=proven,expected=nr['content_sha256'],predicted=h)
 if proven:
  delta=nd.fields((s['i'],s['row'],s['target']),(nr['i'],raw,s['target']))
  fields.update({p for p,_,_ in delta});top.update({p.split('/')[2] if p.startswith('/row/') else p for p,_,_ in delta})
  entry['changes']=[dict(path=p,P=nd.shown(a),N=nd.shown(b)) for p,a,b in delta]
  nbytes+=len(raw)
  sample_rows.append(dict(**{'class':s['class']},position=s['position'],P_i=s['i'],key=nd.key(row),i=nr['i'],row=raw,target=s['target'],content_sha256=h))
 proof.append(entry)
write(D/'SAMPLED_FIELD_PROOFS.json',dict(scope='Predicted stored text accepted only when its typed i,row,target digest equals the published N content_sha256; not a database rebuild.',rows=proof,path_counts=dict(fields),top_counts=dict(top),sample_bytes=nbytes))
print('PROVEN',Counter((p['source'],p['proven']) for p in proof));print('TOP',dict(top));print('PATHS',len(fields),'EST_SIZE',len(nd.raw(proof))+nbytes)
assert len(proof)==73 and all(p['proven'] for p in proof)
recovered=D/'recovered';recovered.mkdir(exist_ok=True)
value=dict(reference,database_sha256=z.load(E/'rd0/rdiff_summary.json')['inputs']['N']['sha256'],count=43101,U_Faithful_count=718,requested=100,rows=sample_rows,absent=missing,
 provenance='Every recovered N i,row,target was checked against its published content_sha256. N SQLite bytes were not locally available.')
(recovered/'n_sample.json').write_bytes(nd.raw(value))
(recovered/'nd.json').write_bytes(nd.raw(dict(schema='sample-proof-v1',matched_samples=73,sample_paths=dict(fields),all_matched_path_counts=None,
 qualification='Full-population path counts require the CPU helper on both databases. These sampled differences have exact N content-hash proofs.',samples=proof)))
print('RECOVERED_BYTES',sum(p.stat().st_size for p in recovered.iterdir()))
