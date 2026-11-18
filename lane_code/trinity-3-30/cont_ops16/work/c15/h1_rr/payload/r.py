"""Bind local login-node evidence. No submission and no credential access."""
import hashlib,importlib.util,json,sys
from pathlib import Path
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dk',B/'d.py');dk=importlib.util.module_from_spec(spec);spec.loader.exec_module(dk)
ids=json.loads((B/'ids.json').read_text());tok=ids['tokens'];O=Path('/project/community/jjyeung/okh7');KH=O/('x_'+tok['kit']);base=O/'x_07ca49df'
def load(p):return json.loads(Path(p).read_text())
def w(p,v):dk.write(p,v)
def manifest(root):return dict(reversed(l.split('  ',1)) for l in (root/'SHA256SUMS.txt').read_text().splitlines())
mode=sys.argv[1]
if mode=='prepare':
 o=load(B/'over.json');result=dk.derive(base,B/'p',o);w(B/'p.json',result)
 sys.path.insert(0,str(B/'p/b'));from d import contract
 la=load(B/'p/k/launch.json');cfg=load(B/'p'/la['config']['file'])
 assert result['config_identity']==ids['identity'] and dk.digest(contract(la,cfg))==ids['contract']
 # Reproduce the complete source kit with empty overrides; all manifest members must be byte-identical.
 dk.derive(base,B/'e',{})
 assert manifest(B/'e')==manifest(base)
 for n,h in manifest(base).items():assert dk.sha(B/'e'/n)==h
 w(B/'e.json',dict(status='PASS',manifest_sha256=dk.sha(base/'SHA256SUMS.txt')))
elif mode=='stage':
 spec=importlib.util.spec_from_file_location('verify',B/'v.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 checks=v.main(B/'p',base/'k/0.json');w(B/'c.json',checks)
 if checks['missing']:raise SystemExit('missing staging inputs')
 w(B/'staging.json',dict(status='PASS',source_revision='sha256:'+ids['tree'],config_sha256=ids['identity'],missing=[],project_community_write_bytes=0,evidence=dict(checks_sha256=dk.sha(B/'c.json'),inherited_scope='availability plus supplied sealed staging attestation; native c.sh rechecks bytes'),scope='read-only changed-payload verification; excludes upload, extraction and derivation writes'))
 # Off-scratch archive exists and was hash-checked during derivation.
 arc=B/ids['trainer']['file'];assert dk.sha(arc)==ids['trainer']['sha256']
 w(B/'archive.json',dict(schema='s1-source-archive-v1',status='ARCHIVED',durable=True,location=str(arc),sha256=dk.sha(arc),tree_sha256=ids['tree'],bytes=arc.stat().st_size,verification_scope='read-back SHA256 on login-node project storage'))
elif mode=='final':
 rv=load(B/'review.json');st=load(B/'staging.json');gate=load(B/'gate.json')
 assert rv['verdict']=='PASS' and rv['reviewer'] and rv['config_sha256']==ids['identity'] and rv['admission_contract_sha256']==ids['contract'] and rv['source_revision']=='sha256:'+ids['tree']
 assert st['status']=='PASS' and st['config_sha256']==ids['identity'] and st['missing']==[]
 assert gate['passes'] is True and gate['source_receipt_sha256']=='9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851'
 o=load(B/'over.json');o['status']='READY'
 for n in ('review.json','staging.json','4.json'):o['add_k'][n]=dict(path=str(B/n),sha256=dk.sha(B/n))
 o['code_tree']['archive_record']=dict(path=str(B/'archive.json'),sha256=dk.sha(B/'archive.json'))
 w(B/'ready.json',o);r=dk.derive(base,KH,o);w(B/'result.json',r)
 # Compare the complete final inventory to a complete temporary derivation, not a FIXTURE launch hash.
 candidate=B/'q';test=dict(o,fixture=True,status='BLOCKED');dk.derive(base,candidate,test)
 la=load(candidate/'k/launch.json');la.update(status='READY',production_authorized=True);w(candidate/'k/launch.json',la)
 man=manifest(candidate);man['k/launch.json']=dk.sha(candidate/'k/launch.json')
 assert man==manifest(KH)
 # Separate ANON content review must cover these exact bytes; never manufacture CLEAN here.
 names={line.split('  ',1)[1] for line in (B/'sums.txt').read_text().splitlines()} | {'ready.json','archive.json','gate.json','c.json','e.json'}
 external=[dict(path=str(B/n),sha256=dk.sha(B/n)) for n in sorted(names)]
 w(B/'anon.json',dict(status='UNREVIEWED',hits=None,manifest_sha256=dk.sha(KH/'SHA256SUMS.txt'),external=external,scope='Final changed records, runtime scripts and trainer contents require content review; inherited identifiers need explicit accounting. This record grants no submission approval.'))
 w(B/'compare.json',dict(status='PASS',manifest_sha256=dk.sha(KH/'SHA256SUMS.txt'),identity=r['config_identity'],contract=ids['contract'],config_key=r['config_key']))
elif mode=='certify':
 cert=load(B/'anon.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert['manifest_sha256']==dk.sha(KH/'SHA256SUMS.txt')
 for p in cert['external']:assert dk.sha(p['path'])==p['sha256']
 w(KH/'ANON_OK.json',cert)
 sys.path.insert(0,str(KH/'b'));import a;a.main(KH)
else:raise SystemExit('unknown mode')
