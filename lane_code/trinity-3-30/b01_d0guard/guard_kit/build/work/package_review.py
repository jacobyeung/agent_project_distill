import ast,difflib,hashlib,io,json,pathlib,re,tarfile
B=pathlib.Path(__file__).resolve().parents[1];A=B.parents[1];O=B/'out';K=O/'guard_kit';S=A/'work/c8r_code'
import sys
sys.path.insert(0,str(K));from guard_core import read,write,sha,digest
from names import scan_json
for p in K.rglob('*.py'):compile(p.read_text(),str(p),'exec')
# Reviewed checker sources are supplied without modification.
for name in ('export_check.py','common.py'):
 source=A/'work/from13/readk/kit/reader/out'/name
 target=K/'reviewed/checker'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(source.read_bytes())
# Keep reference/item inputs separate from the executable archive.
def pack(target,files):
 members={}
 with tarfile.open(target,'w',format=tarfile.USTAR_FORMAT) as t:
  for name,path in sorted(files.items()):
   data=path.read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755 if path.suffix=='.sh' else 0o644
   info.mtime=0;info.uid=0;info.gid=0;info.uname='';info.gname='';t.addfile(info,io.BytesIO(data));members[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 with tarfile.open(target) as t:
  rows=list(t);assert all(m.isfile() for m in rows);assert len({m.name for m in rows})==len(rows)
 return dict(bytes=target.stat().st_size,sha256=sha(target),members=members,regular_members_only=True)
code=pack(O/'code_g1.tar',{str(p.relative_to(K)):p for p in K.rglob('*') if p.is_file()})
inputs=pack(O/'inputs_g1.tar',{n:O/'inputs'/n for n in ('reference.json','items.json')})
(O/'code_g1.tar.sha256').write_text(code['sha256']+'  code_g1.tar\n')
(O/'inputs_g1.tar.sha256').write_text(inputs['sha256']+'  inputs_g1.tar\n')
write(O/'CODE_MANIFEST.json',code);write(O/'INPUT_MANIFEST.json',inputs)
C=read(O/'BASELINE_CONFIG.json');selection=read(O/'ITEM_SELECTION.json')
blockers=['Candidate training configuration/preparation/data receipt/source-seal closure is not supplied.',
          'Production dual-export staging, worker launch, early receipt publication and packet bootstrap are not integrated.',
          'Complete job-visible naming migration is not implemented.',
          'Whole-worker production-CONFIG CPU rehearsal has not completed; namespace probe failed.',
          'New source/object admissions, independent review and cloud generations remain pending.']
family=dict(schema='g1-review-family-v1',release_ready=False,blockers=blockers,steps=[200,400,600,800,1000],run='359fcc3c',
 time_limit='05:00:00',gpus=1,partition='general',
 code=dict(name='q8/8c9d2e74/c_'+code['sha256'][:16]+'.tar',bytes=code['bytes'],sha256=code['sha256'],generation='PENDING_UPLOAD'),
 inputs=dict(name='q8/8c9d2e74/i_'+inputs['sha256'][:16]+'.tar',bytes=inputs['bytes'],sha256=inputs['sha256'],generation='PENDING_UPLOAD'),
 independent=dict(sha256=sha(O/'INDEPENDENT_CONTRACT.json'),baseline_family_sha256=sha(B/'in_c8r_kit/FAMILY.json')),
 proof_transport=C['transport'],reference=dict(member='reference.json',sha256=sha(O/'inputs/reference.json')),
 distance_list=dict(sha256=selection['distance_list']['sha256'],items=150),items=dict(member='items.json',sha256=sha(O/'inputs/items.json')),
 code_pins={name:entry['sha256'] for name,entry in code['members'].items()})
write(O/'FAMILY.json',family)
# A unified source diff and one row per changed/additional file.
patch=[];table=['# Source changes','', 'All original C8r source files remain byte-identical (`SOURCE_IDENTITY.json`). Added modules are a partial review implementation. Production packet integration is incomplete.', '', '| File | Lines | Change | Reason | Brief item |','|---|---|---|---|---|']
notes={'guard_core.py':('Strict completion receipt, identity comparison and proof/canary sequencing','Fail closed on foreign exports and proof mismatch','1, 3, 4, 5'),
'native_arm.py':('Select native AST prefix and one refusal row','Preserve sealed kernels and omit scripted serving','3'),
'guard_export.py':('Wrap unchanged reviewed stager with plan-bound plain-text receipt','Check candidate identity, bytes and digest before extraction','1'),
'guard_backend.py':('Authenticate candidate metadata and prepare/serve using C8r','Preserve restoration checks; candidate closure required','1, 2, 3'),
'names.py':('Reversible name substitutions and occurrence scanner','Audit name-only edits without modifying other JSON values','6'),
'packet.py':('Draft-plan preparation, regular-tar checks, resource arguments and explicit release refusal','Prevent incomplete kit from launching','1, 6, 7')}
for p in sorted(K.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(K);old=S/rel
 if old.is_file() and old.read_bytes()==p.read_bytes():continue
 if p.suffix not in ('.py','.json','.sh'):continue
 before=old.read_text().splitlines(True) if old.is_file() else [];after=p.read_text().splitlines(True)
 patch.extend(difflib.unified_diff(before,after,fromfile='c8r/'+str(rel),tofile='guard_kit/'+str(rel)))
 change,reason,item=notes.get(str(rel),('Copy reviewed dependency unchanged','Keep reviewed export-admission semantics and full checker','1'))
 table.append('| `guard_kit/'+str(rel)+'` | 1–'+str(len(after))+' | '+change+' | '+reason+' | '+item+' |')
(O/'DIFF.patch').write_text(''.join(patch));(O/'DIFF.md').write_text('\n'.join(table)+'\n')
write(O/'RELEASE_BLOCKERS.json',dict(status='NOT_READY',blockers=blockers,naming_family_occurrences=scan_json(family)))
print(json.dumps(dict(code_sha256=code['sha256'],code_bytes=code['bytes'],input_sha256=inputs['sha256'],input_bytes=inputs['bytes'],family_sha256=sha(O/'FAMILY.json'),status='NOT_READY'),indent=2))
