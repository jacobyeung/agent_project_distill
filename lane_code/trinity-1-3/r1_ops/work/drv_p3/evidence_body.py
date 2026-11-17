import copy,hashlib,importlib.util,json,os,stat,sys,tarfile
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_@STORE@');H=B.parent/'x_3fdda0fb';OLD=B.parent/'i_1be16f28'
MAN='@SOURCE_MANIFEST@'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,d):
 with p.open('x') as f:json.dump(d,f,sort_keys=True,separators=(',',':'));f.write('\n')
def make_records(b,h,old,ev,checks,review_input):
 ids=load(b/'ids.json');binding=load(b/'BINDING.json');code=load(b/'c.json')
 ident=ids['identity'];revision='sha256:'+binding['tree_sha256'];arc=b/'t.tar'
 st=copy.deepcopy(load(old/'staging.json'))
 st.update(status='PASS',source_revision=revision,config_sha256=ident,missing=[],project_community_write_bytes=0,
  evidence=dict(checks_sha256=sha(ev/'c.json'),inherited_staging_sha256=sha(h/'k/staging.json'),inherited_scope='availability plus supplied sealed staging attestation; native c.sh rechecks bytes'),
  scope='read-only changed-payload verification; excludes upload, extraction and derivation writes')
 ar=copy.deepcopy(load(old/'archive.json'))
 ar.update(schema='s1-source-archive-v1',status='ARCHIVED',durable=True,location=str(arc),sha256=sha(arc),tree_sha256=binding['tree_sha256'],bytes=arc.stat().st_size,verification_scope='read-back SHA256 on login-node project storage')
 rv=copy.deepcopy(load(old/'review.json'))
 rv.update(verdict='PASS',reviewer=', '.join(review_input['reviewers']),reviewers=review_input['reviewers'],config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],admission_scope='pinned-template-and-native-data-derivation',attestation='The five-review chain ends with review_r1p5 accepting the final packet; production CPU preparation proof remains required.',evidence=review_input)
 au=copy.deepcopy(load(old/'4.json'))
 # Inherit the envelope, never the H1 production permissions or source-specific attestations.
 for k in ('written_authorization','written_authorizations','admission_evidence','omission_authority'):au.pop(k,None)
 au.update(config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],partition='general',allowed_partitions=['general','advanced'],account='mt01',modes=['p'],new_gpus={'p':0},gpu_cap=4,max_parallel_jobs=1,production_go_granted=False,production_go_required_separately=True,full_population_admission=False,native_memory_sufficiency_proven=False,review=None,scope='One mode-p CPU proof; production GO remains pending.',wall_seconds=14400,allocation_memory_gib=800,conditions=['One CPU proof; refuse any a15_cot_ap or jjy_ job on the requested partition.','The final manifest requires independent content certification.','Production submission requires a separate identity-bound GO.'])
 for n,d in [('review.json',rv),('staging.json',st),('archive.json',ar),('4.json',au)]:write(ev/n,d)

def evidence(b,h,old,ev,verify):
 ids=load(b/'ids.json');binding=load(b/'BINDING.json');code=load(b/'c.json');cfg=load(b/'config.json')
 ident=ids['identity'];revision='sha256:'+binding['tree_sha256']
 assert code['commit']==revision and ident==binding['config_identity']
 # Require the operator's uploaded exact-packet independent verdict record.
 review_input=load(b/'r1.json')
 assert review_input['config_sha256']==ident and review_input['source_revision']==revision
 assert review_input['operator_archive_sha256']=='@OUTER@'
 texts={short:(b/short).read_bytes().decode() for short in REVIEW_FILES}
 assert review_input==build_chain(texts,ident,binding['tree_sha256'],'@OUTER@'), 'Review chain differs'
 assert sha(h/'SHA256SUMS.txt')==MAN
 manifest=dict(reversed(x.split('  ',1)) for x in (h/'SHA256SUMS.txt').read_text().splitlines())
 for n in ('k/0.json','k/staging.json','k/review.json','k/archive.json','k/4.json'):
  assert sha(h/n)==manifest[n], 'H1 source evidence differs'
 inherited=load(h/'k/staging.json')
 assert inherited['status']=='PASS' and inherited['missing']==[] and inherited['project_community_write_bytes']==0
 # Use the H1 bundle schemas; require the sealed kit's corresponding records to agree.
 for n in ('review.json','staging.json','archive.json','4.json'):
  assert load(old/n)==load(h/'k'/n), 'H1 bundle evidence differs from sealed kit: '+n
 ev.mkdir(mode=0o700)
 arc=b/'t.tar';assert sha(arc)==code['archive']['sha256']
 files={}
 with tarfile.open(arc) as tf:
  for m in tf:
   assert m.isfile() and m.name in code['files'] and m.name not in files
   files[m.name]=hashlib.sha256(tf.extractfile(m).read()).hexdigest()
 assert files==code['files']
 assert hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()==binding['tree_sha256']
 # Mirror only d.py's staging-record additions. No archive extraction or data copy is needed.
 cur=load(h/'k/0.json');extra={}
 extra[str(Path(cfg['streams']['vqa']['path']).parent/'d.db')]={'parts':[binding['orchard_store']],'sha256':binding['database_sha256']}
 store=Path(binding['orchard_store']);assert not store.is_symlink() and stat.S_IMODE(store.stat().st_mode)==0o400
 assert binding.get('unit_binding'), 'Proof 2 requires the unit source'
 for name,value in binding['unit_binding']['artifacts'].items():
  assert sha(b/name)==value['sha256'], 'Unit artifact differs: '+name
  extra[value['path']]={'parts':[str(b/name)],'sha256':value['sha256']}
 prefix='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'+binding['store_key']
 for name in binding['record_files']:
  assert sha(b/name)==sha(b/'records'/name)
  extra[prefix+'/'+name]={'parts':[str(b/name)],'sha256':sha(b/'records'/name)}
 assert sha(b/'s.json')==sha(b/'proof/selection/r.json')==binding['selection_sha256']
 extra[prefix+'/s.json']={'parts':[str(b/'s.json')],'sha256':sha(b/'s.json')}
 for dest,item in extra.items():
  assert all(x.get('dest')!=dest for x in cur.get('extra',[]))
  cur.setdefault('extra',[]).append(dict(dest=dest,**item))
 stage=ev/'s';(stage/'k').mkdir(parents=True,mode=0o700)
 write(stage/'k/0.json',cur)
 checks=verify(stage,h/'k/0.json');write(ev/'c.json',checks)
 assert checks['missing']==[], 'missing staging inputs'
 make_records(b,h,old,ev,checks,review_input)
 print('PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false')
if __name__=='__main__':
 # STAGING_VERIFY is the byte-for-byte H1 payload/v.py module embedded by the builder.
 scope={'__name__':'inherited_staging'};exec(compile(STAGING_VERIFY,'v.py','exec'),scope)
 evidence(B,H,OLD,B/'e',scope['main'])
