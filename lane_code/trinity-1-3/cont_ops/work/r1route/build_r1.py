from pathlib import Path
import ast,hashlib,json,tarfile,io,sys,secrets,difflib
W=Path(__file__).resolve().parent
F=Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
config=W/'in/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json'
data=W/'in/inputs/data_receipt.json';c=json.loads(config.read_text())
binding=dict(run='673bc60f',step=200,member_directory='m200',lineage='SFT',object='q8/8865619b/673bc60f_m200.tar',
 config_sha256='620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a',base_identity=c['base_identity'],frame_layout='duplicate',
 preparation_sha256=dict(config=sha(config.read_bytes()),receipt=c['preparation']['sha256'],data_receipt=sha(data.read_bytes())))
dump(W/'out/EXPORT_BINDING.json',binding)
compat='''\n# Python 3.6 login/node helpers retain the same containment semantics.\nif not hasattr(Path, 'is_relative_to'):\n    def _is_relative_to(self, other):\n        try:self.relative_to(other);return True\n        except ValueError:return False\n    Path.is_relative_to = _is_relative_to\n'''
admission='''\n    binding = cfg.get('export_binding')\n    if binding is not None:\n        for key in ('run', 'step', 'member_directory', 'lineage', 'object'):\n            if export.get(key) != binding[key]:raise ValueError('Reviewed export binding differs: '+key)\n        for name, digest in binding['preparation_sha256'].items():\n            if export['preparation'][name]['sha256'] != digest:\n                raise ValueError('Reviewed preparation differs: '+name)\n        if export.get('config_sha256') != binding['config_sha256']:\n            raise ValueError('Reviewed config identity differs')\n        if export.get('archive_sha256') != inputs['archives'][0]['sha256']:\n            raise ValueError('Reviewed archive differs')\n'''
fill_extra='''\ndef reviewed_binding():\n    package = Path(__file__).resolve().parent.parent\n    if not (package/'0.tgz').is_file():package = Path(__file__).resolve().parent/'package'\n    public = json.loads((package/'0.json').read_text())\n    raw = (package/'0.tgz').read_bytes()\n    if pin(raw)['sha256'] != public['payload_sha256']:raise ValueError('Reviewed payload differs')\n    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:\n        cfg = json.load(archive.extractfile('9.json'))\n    digest = hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest()\n    if digest != public['plan_sha256']:raise ValueError('Reviewed plan differs')\n    return cfg['export_binding']\n\ndef bind_review(a, export, artifact, archive, prep, binding):\n    for key, actual in [('object',a.object),('step',a.step),('lineage',a.lineage),\n                        ('member_directory',export['member_directory'])]:\n        if actual != binding[key]:raise ValueError('Reviewed export binding differs: '+key)\n    if artifact.get('step') != binding['step']:raise ValueError('Artifact step differs')\n    for key in ('config_sha256','base_identity','frame_layout'):\n        if artifact.get(key) != binding[key]:raise ValueError('Artifact identity differs: '+key)\n    for name in ('heads','full_weights'):\n        path = PurePosixPath(artifact[name]['path'])\n        tail = PurePosixPath(binding['run'])/binding['member_directory']/MEMBERS[name]\n        if path.parts[-len(tail.parts):] != tail.parts:raise ValueError('Artifact run/member path differs')\n    for name, digest in binding['preparation_sha256'].items():\n        if prep[name]['sha256'] != digest:raise ValueError('Reviewed preparation differs: '+name)\n    export.update(run=binding['run'],object=binding['object'],config_sha256=binding['config_sha256'],\n                  archive_sha256=archive['sha256'])\n\n'''
for kind in ('b1','b2'):
 O=W/'out'/kind;P=O/'package';base=F/kind
 # Build deterministically from the reviewed base, never from a prior local build.
 with tarfile.open(base/'0.tgz') as t:payload={m.name:t.extractfile(m).read() for m in t}
 old=dict(payload);cfg=json.loads(payload['9.json']);token=(O/'TOKEN').read_text().strip()
 if token[0] not in 'abcdef':
  token=secrets.choice('abcdef')+token[1:];(O/'TOKEN').write_text(token+'\n')
 cfg.update(token=token,export_binding=binding,stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
 for n in ('8.py','orchard_h10/common.py','orchard_h10/job.py'):
  s=payload[n].decode()
  s=s.replace("Path('/project/community/jjyeung')/cfg['token']","Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+cfg['token'])")
  s=s.replace("'/project/community/jjyeung/'+cfg['token']","'/project/community/jjyeung/okh7/a15_cot_ap'+cfg['token']")
  s=s.replace("Path('/project/community/jjyeung')/public['token']","Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+public['token'])")
  s=s.replace("with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()", "h=hashlib.sha256()\n    with Path(path).open('rb') as stream:\n        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)\n    return h.hexdigest()")
  s=s.replace("    with Path(path).open('rb') as stream:\n        return hashlib.file_digest(stream, 'sha256').hexdigest()", "    h=hashlib.sha256()\n    with Path(path).open('rb') as stream:\n        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)\n    return h.hexdigest()")
  s=s.replace('capture_output=True','stdout=subprocess.PIPE,stderr=subprocess.PIPE').replace('text=True','universal_newlines=True')
  if n.endswith('common.py'):s=s.replace('\nORDER =',compat+'\nORDER =')
  if n.endswith('job.py'):
   s=s.replace("        export_pins=load(inputs,shared)","        export_pins=load(inputs,shared)\n        write(out/'metadata/EXPORT_PIN.json',export_pins)\n        write(out/'metadata/INPUTS.json',inputs)")
  payload[n]=s.encode()
 # No vendor semantics change: compatible keyword spellings only.
 for n in list(payload):
  if n.startswith('orchard_h10/vendor/') and n.endswith('.py'):
   s=payload[n].decode().replace('capture_output=True','stdout=subprocess.PIPE,stderr=subprocess.PIPE').replace('text=True','universal_newlines=True')
   payload[n]=s.encode()
   if Path(n).name in cfg['template_pins']:cfg['template_pins'][Path(n).name]=sha(payload[n])
 n='orchard_h10/export_pins.py';s=payload[n].decode();s=s.replace("    root = Path(cfg['logical'])",admission+"    root = Path(cfg['logical'])");payload[n]=s.encode()
 # Preserve all serving source bytes. Operator chooses only the requested read.
 sequence=(base/'tower_sequence.py').read_text()
 if kind=='b1':
  start=sequence.index('RULES=');end=sequence.index('\ndef sealed_write')
  sequence=sequence[:start]+'''RULES=('candidates_argmax',)
COUNTS=(150,150,150,150,36)
SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4))

def descriptors(package):
 return [dict(arm='tower',modes=['none'],stage1_select_rule='candidates_argmax',save_own_depth=False,
              perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
              types=[3,0,1,2,4],expected=636)]
''' +sequence[end:]
  sequence=sequence.replace("('verify' if i==1 else 'on')","'on'").replace('expected=636 if i==0 else 150','expected=636').replace('for i in (1,0):','for i in (0,):').replace('for i,n in ((0,636),(1,150)):','for i,n in ((0,636),):').replace('expected=786','expected=636').replace('captures=(84,60)','captures=(84,)')
 else:sequence=sequence.replace('null_argmax','candidates_argmax')
 sequence=sequence.replace("(-1 if rule==RULES[0] else 1)",'1')
 (O/'tower_sequence.py').write_text(sequence)
 node=(base/'node_check.py').read_text().replace("!='null_argmax'","!='candidates_argmax'").replace("!='off'","!='on'")
 node=node.replace("ast.unparse(expression.func) != 'bytes.fromhex'","not (isinstance(expression.func,ast.Attribute) and isinstance(expression.func.value,ast.Name) and expression.func.value.id=='bytes' and expression.func.attr=='fromhex')")
 (O/'node_check.py').write_text(node)
 boot=(base/'tower_bootstrap.py').read_text().replace("Path('/project/community/jjyeung')/public['token']","Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+public['token'])")
 (O/'tower_bootstrap.py').write_text(boot)
 fill=(base/'fill_export.py').read_text();fill=fill.replace('\ndef main():','\n'+fill_extra+'\ndef main():')
 fill=fill.replace('    if a.step < 0:',"    binding=reviewed_binding()\n    if (a.object != binding['object'] or a.step != binding['step'] or a.lineage != binding['lineage']):\n        raise ValueError('Reviewed run/step/object differs')\n    if len(a.parts) != 4:raise ValueError('Require four ordered parts')\n    if a.step < 0:")
 fill=fill.replace("    export.update(schema=", "    bind_review(a,export,artifact,archive,prep,binding)\n    export.update(schema=")
 fill=fill.replace("    inputs['types']=['camera_displacement','camera_rotation','camera_movement_direction']", "    # Preserve the reviewed item selection from the base input plan.")
 # Existing prep archive index 4 must be replaced, not overlaid after newer data.
 fill=fill.replace("    inputs['archives'].append(dict(destination=archive['destination'],parts=[prep_archive],\n                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values()))))", "    inputs['archives'][4]=dict(destination=archive['destination'],parts=[prep_archive],\n                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values())))")
 (O/'fill_export.py').write_text(fill);(P/'a/4.py').write_text(fill)
 cfg['payload_pins']={n:dict(bytes=len(b),sha256=sha(b)) for n,b in payload.items() if n!='9.json'}
 payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
 for n,b in payload.items():
  p=O/'src'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 sys.path.insert(0,str(O/'src'))
 # Local serializer is deliberately independent of importing a modified vendor cache.
 def tarbytes(files):
  buf=io.BytesIO()
  import gzip
  with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for n,b in sorted(files.items()):
     m=tarfile.TarInfo(n);m.size=len(b);m.mode=0o600;t.addfile(m,io.BytesIO(b))
  return buf.getvalue()
 raw=tarbytes(payload);(P/'0.tgz').write_bytes(raw);(O/'0.tgz').write_bytes(raw)
 public=dict(token=token,payload_sha256=sha(raw),payload_bytes=len(raw),plan_sha256=sha(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()))
 dump(P/'0.json',public);dump(P/'CONFIG.json',public)
 from orchard_h10.build import batch
 bundle=tarbytes({'0.py':boot.encode(),'7.py':sequence.encode(),'0.json':(P/'0.json').read_bytes()})
 (P/'BATCH.sh').write_text(batch(bundle,token))
 (P/'a/5.py').write_text(node);(P/'a/6.py').write_text(sequence)
 inputs=json.loads((base/'inputs_tower.json').read_text())
 # A sealed but unresolved binding cannot accidentally admit the step-544 base.
 dump(P/'a/0.json',inputs);dump(O/'inputs_tower.json',inputs)
 dump(P/'a/1.json',dict(pending=True));dump(P/'a/export.json',dict(pending=True))
 immutable=('0.tgz','0.json','3.py','BATCH.sh','CONFIG.json','a/0.json','a/4.py','a/5.py','a/6.py')
 manifest=dict(token=token,files={n:sha((P/n).read_bytes()) for n in immutable})
 dump(P/'PACKAGE.json',manifest);dump(O/'PACKAGE.json',manifest)
 plan=json.loads((base/'READ_PLAN.json').read_text());plan.update(token=token,expected=[636 if kind=='b1' else 134],rules=['candidates_argmax'],sequence=[[0,t] for t in ([3,0,1,2,4] if kind=='b1' else [4])],read_settings=[dict(arm='tower',modes=['none'],stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=[3,0,1,2,4] if kind=='b1' else [4],expected=636 if kind=='b1' else 134)],export_binding=binding,plan_sha256=public['plan_sha256'],operator_sha256=sha(sequence.encode()),operations_file='OPERATIONS_R1ROUTE.md')
 plan.pop('commands',None);plan['cpu_check'].update(helper_sha256=sha(node.encode()),bootstrap_sha256=sha(boot.encode()))
 dump(O/'READ_PLAN.json',plan)
 changed=[n for n in sorted(old.keys()|payload.keys()) if old.get(n)!=payload.get(n)]
 dump(O/'PAYLOAD_CHANGES.json',changed)
 patch=[];rows=['file\tbase_sha256\tnew_sha256']
 for n in changed:
  rows.append(n+'\t'+sha(old.get(n,b''))+'\t'+sha(payload.get(n,b'')))
  a=old.get(n,b'').decode().splitlines(True);b=payload.get(n,b'').decode().splitlines(True)
  if n=='9.json':a=json.dumps(json.loads(old[n]),indent=2,sort_keys=True).splitlines(True);b=json.dumps(cfg,indent=2,sort_keys=True).splitlines(True)
  patch.extend(difflib.unified_diff(a,b,fromfile='base/'+n,tofile='payload/'+n))
 for n in ('tower_sequence.py','tower_bootstrap.py','node_check.py','fill_export.py'):
  a=(base/n).read_bytes();b=(O/n).read_bytes();rows.append(n+'\t'+sha(a)+'\t'+sha(b));patch.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='base/'+n,tofile='operator/'+n))
 (O/'PATCH.diff').write_text(''.join(patch));(O/'FILE_SHA256_DIFF.tsv').write_text('\n'.join(rows)+'\n')
 files={str(p.relative_to(P)):p.read_bytes() for p in P.rglob('*') if p.is_file()}
 (O/'1.tgz').write_bytes(tarbytes(files))
 print(kind,token,sha(raw),len(raw),changed)
