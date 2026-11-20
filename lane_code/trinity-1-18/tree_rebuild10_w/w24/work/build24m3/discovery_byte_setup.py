from common import *
s=(D/'discovery_shell.py').read_text().replace("F=D/'discovery_shell_v2'","F=D/'discovery_shell_protected_bytes'")
start=s.index("prepared=J.load(");end=s.index("\nselection=J.load",start)
s=s[:start]+'''import sqlite3,copy
prepared=J.load(D/'census_final/qd_clean/cfg.json')
pins={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
pins.update({p.name:str(p) for p in (D/'u').iterdir()})
def local(v):
 if isinstance(v,dict):
  return {n:(pins[v['sha256']] if n=='path' and v.get('sha256') in pins else local(x)) for n,x in v.items()}
 if isinstance(v,list):return [local(x) for x in v]
 return v
prepared=local(prepared)
prepared['r1_training']={k:prepared['r1_training'][k] for k in ('room_authority','launch22','proof_mode')}
prep=dict(streams={},remove_files=prepared['remove_files'],r1_training=prepared['r1_training']);source={}
listed=[json.loads(x) for x in (D/'u/d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1').read_text().splitlines()]
def db(name,rows):
 path=F/name
 with sqlite3.connect(path) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  for j,row in enumerate(rows):c.execute('insert into rows values(?,?,?)',(j,json.dumps(row),'{}'))
 return dict(path=str(path),sha256=J.sha(path))
for stream in ('pose','vqa','routing','pointing'):
 rows=[dict(qid=stream+str(j),canonical='scannet/scene9999_00',dataset='scannet',scene='scene9999_00',target='<think>The fixture supplies this observation.</think>A') for j in range(64)]
 if stream=='pointing':rows[-1].update(qid=listed[0]['row_key'],provenance=dict(canonical_scene=listed[0]['canonical']))
 actual=db(stream+'.sqlite',rows);receipt=J.write(F/(stream+'.json'),dict(database=actual,count=len(rows)))
 prepared['streams'][stream]=receipt;prep['streams'][stream]=dict(database=actual,receipt=receipt,count=len(rows))
 original=rows if stream!='pointing' else [dict(row_key=r['row_key'],provenance=dict(canonical_scene=r['canonical'])) for r in listed]+rows
 population=db(stream+'_source.sqlite',original)
 sr=J.write(F/(stream+'_source.json'),dict(database=population,count=len(original)))
 source[stream]=[dict(receipt=sr,population=population,count=len(original))]
prepared['preparation']=J.write(F/'prep.json',prep)
prepared['r1_training'].pop('review',None);prepared['r1_training'].pop('init_policy',None);prepared['r1_training']['proof_mode']='q'
J.write(F/'prepared.json',prepared);J.write(F/'source.json',source)
'''+s[end:]
s=s.replace(" host=z.write(root/'q/host.json',", """ sp=z.write(root/'q/ss.json',z.load(F/'source.json'))
 mp=z.write(root/'i/staging.json',dict(entries={'ss.json':dict(sha256=sp['sha256'],bytes=(root/'q/ss.json').stat().st_size)}))
 host=z.write(root/'q/host.json',""")
s=s.replace("staging_plan_sha256='1'*64","staging_plan_sha256=mp['sha256']")
needle=" config=z.write(root/'prepared.json',cfg)"
s=s.replace(needle,""" from cs import publish
 publish(Path(__file__).resolve().parents[1],root.parent,cfg,os.environ['SLURM_JOB_ID'])
 z.write(root.parent/'PREPARATION_CONTINUED.json',dict(prepared=True,census='WOULD_REFUSE'))
"""+needle)
s=s.replace("assert J.load(node/'p/hr.json')==J.load(node/'p/q/host.json')","""host=J.load(node/'p/hr.json');assert host['protected_census']['sha256']==J.sha(node/'c5.json')
assert J.load(node/'c5.json')['status']=='WOULD_REFUSE'
assert J.load(node/'c5.json')['streams']['pointing']['status']=='WOULD_REFUSE'
assert J.load(node/'PREPARATION_CONTINUED.json')['prepared']""")
s=s.replace("D/'DISCOVERY_SHELL_TESTS.json'","D/'DISCOVERY_CENSUS_SHELL_TESTS.json'")
s=s.replace("h_real=True,rv_real=True,","h_real=True,rv_real=True,cs_native_postcondition=True,protected_pointing_would_refuse=True,")
s=s.replace("'Native regeneration/digest and native donor handover are tested separately'","'Native regeneration/digest and native donor handover are tested separately','Native cs.publish consumes complete synthetic source and admitted stores; h.py pins the WOULD_REFUSE receipt; rv.py continues to WAITING_REVIEW'")
s=s.replace("tail=decoded[decoded.index('# Both invocations'):]", "tail=decoded[decoded.index('# Both invocations'):].replace('/usr/bin/python3',shlex.quote(sys.executable))")
(D/'discovery_census_shell.py').write_text(s)
