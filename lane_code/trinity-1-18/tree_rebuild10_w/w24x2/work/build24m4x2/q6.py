from pathlib import Path
import sys,json,sqlite3,copy,importlib.util
from unittest.mock import patch
L=Path.cwd();D=L/'work/build24m4x2';sys.path[:0]=[str(L/'out/rcj'),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import ch,z
from student_pilot.extent_receipt import Extents,required
from student_pilot.p3_provenance import file_pin
F=D/'q6';F.mkdir();names=z.load(D/'SOURCES.json')['names'];cfg=dict(extent_receipt=file_pin(D/'c072905b.json'),r1_training=dict(extent_pool_sources=names))
rows=[json.loads(v['row']) for v in z.load(D/'published/p_sample.json')['rows'] if not json.loads(v['row'])['qid'].startswith('a0_')];assert len(rows)==80
pool=next(r for r in rows if Extents(cfg['extent_receipt'],names).exempt(r,'routing'))
for value in ({},None):assert not Extents(cfg['extent_receipt'],names).exempt(dict(pool,r1_source=value),'routing')
records=[]
for label in ('pass','extra','missing'):
 root=F/label;(root/'selection').mkdir(parents=True);out=root/'out';out.mkdir();values=copy.deepcopy(rows)
 if label=='extra':
  r=next(r for r in values if not required(r,'routing') and 'r1_source' not in r);r['s1_source']=dict(name=names[0])
 if label=='missing':next(r for r in values if Extents(cfg['extent_receipt'],names).exempt(r,'routing'))['s1_source']['name']='unlisted'
 with sqlite3.connect(root/'selection/rows.sqlite') as c:
  c.execute('create table rows(i integer primary key,row text,target text)');c.executemany('insert into rows values(?,?,?)',[(i,json.dumps(r),'{}') for i,r in enumerate(values)])
 with patch.object(ch,'scope_report',return_value=dict(status='PASS',fixture='scope controls tested separately on real rows')):
  result=ch.run(cfg,root,out)
 got=z.load(out/'chain.json');assert got==json.loads(ch.raw(result))
 for key in ('refused_rows','extent_exempted_rows','extent_still_checked_rows'):
  assert got[key]==got['streams']['routing'][key]
 assert got['extent_base_refused_rows']==14
 assert got['status']==('PASS' if label=='pass' else 'FAIL')
 if label=='extra':assert (got['refused_rows'],got['extent_exempted_rows'],got['extent_set_mismatch_rows'])==(0,15,1)
 if label=='missing':assert got['extent_exempted_rows']==13 and got['refused_rows']==1
 records.append(dict(case=label,status=got['status'],routing=got['streams']['routing'],top_level={k:got[k] for k in ('refused_rows','extent_exempted_rows','extent_still_checked_rows')}))
# Exercise actual x.publish return code with otherwise successful publication dependencies.
spec=importlib.util.spec_from_file_location('pub_cases',D/'publication_tests.py');m=importlib.util.module_from_spec(spec);exec(compile((D/'publication_tests.py').read_text().split('\nr=unittest.TextTestRunner')[0],str(D/'publication_tests.py'),'exec'),m.__dict__)
case=m.Tests();oldwrite=m.z.write;current=None
for record in records:
 def injected(path,value):
  if Path(path).name=='chain.json':value=z.load(F/record['case']/'out/chain.json')
  return oldwrite(path,value)
 with patch.object(m.z,'write',side_effect=injected):rc,files,timing=case.publication(m.x,'q6_'+record['case'],'r',0)
 assert rc==int(record['case']!='pass'),(record['case'],rc)
 record['publication_returncode']=rc;record['published_chain_status']=json.loads(files['chain.json'])['status']
prod=z.load(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173796/173796/chain.json'))
report=dict(status='PASS',cases=records,F3_present_empty_or_null_checked=True,production_existing_path='$.streams.routing',new_paths=['$.refused_rows','$.extent_exempted_rows','$.extent_still_checked_rows'],production_prior_counts={k:prod['streams']['routing'][k] for k in ('rows_checked','refused_rows','extent_exempted_rows','extent_still_checked_rows')})
(D/'Q6.json').write_text(json.dumps(report,indent=2)+'\n');print('Q6 PASS: top-level counters, exact set/count checks, publication exits 0/1/1')
