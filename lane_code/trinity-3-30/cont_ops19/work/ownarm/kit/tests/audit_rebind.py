"""Audit a rebind against b200 and write complete script diffs and syntax evidence.

Usage: python audit_rebind.py BUILD FRESH_WORK_DIR DIFF_OUTPUT
"""
import difflib,json,re,subprocess,sys
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(KIT))
import build_ownread as B

def main(build,work,diff_output):
 build=Path(build);work=Path(work);work.mkdir(parents=True,exist_ok=False)
 base=KIT.parent/'out/pkg/b200';raw=(build/'1.tgz').read_bytes()
 old=B.unpack((base/'1.tgz').read_bytes());new=B.unpack(raw)
 op=B.unpack(old['0.tgz']);np=B.unpack(new['0.tgz'])
 oldcfg=json.loads(op['9.json']);newcfg=json.loads(np['9.json'])
 pin=json.loads((build/'BUILD.json').read_text())['export_pin']
 assert set(old)==set(new) and set(op)==set(np)
 assert [n for n in op if op[n]!=np[n]]==['9.json']
 assert {k for k in oldcfg if oldcfg[k]!=newcfg[k]}=={'token','export_binding'}
 assert new['a/6.py']==old['a/6.py']==(build/'tower_sequence.py').read_bytes()
 # Reproduce the exact new archive using only the permitted input changes.
 expected=dict(old);payload=dict(op);B.repin(expected,payload,pin)
 _,_,_,_,rebuilt=B.seal(expected,payload,B.bundle_of(old['BATCH.sh']),newcfg['token'],old['a/6.py'])
 assert rebuilt==raw,'Changes exceed token and export rebind'
 oldplan=json.loads((base/'READ_PLAN.json').read_text());plan=json.loads((build/'READ_PLAN.json').read_text())
 plan_changes=sorted(k for k in set(oldplan)|set(plan) if oldplan.get(k)!=plan.get(k))
 assert plan_changes==['export_binding','plan_sha256','token'],plan_changes
 for n in ('fetch_return.py','unpack_return.py','tower_sequence.py','OPERATOR.md'):
  assert (base/n).read_bytes()==(build/n).read_bytes(),n
 scripts={};lines=['PASS: delivery reproduces b200 with only token, export_binding and REVIEWED_* changes.\n',
  'PASS: operator, tower settings, item order and all payload code are byte-identical.\n',
  'PASS: READ_PLAN.json changes only export_binding, plan_sha256 and token.\n',
  'BUILD.json records build provenance; manifests and archive hashes follow the rebind.\n',
  'Preparation copies and the existing hash guard run before gsutil in both pull scripts.\n\n']
 for n in sorted(old):
  lines.append('delivery %s: %s\n'%(n,'IDENTICAL' if old[n]==new[n] else 'CHANGED (permitted; exact reseal verified)'))
 lines.append('\nPayload: %d/%d members identical; only 9.json differs.\n'%(len(op)-1,len(op)))
 lines.extend(difflib.unified_diff(old['a/4.py'].decode().splitlines(True),new['a/4.py'].decode().splitlines(True),fromfile='b200/package/a/4.py',tofile='r400/package/a/4.py'))
 lines.extend(difflib.unified_diff(B.jbytes(oldcfg['export_binding']).decode().splitlines(True),B.jbytes(newcfg['export_binding']).decode().splitlines(True),fromfile='b200/export_binding',tofile='r400/export_binding'))
 for name in sorted(p.name for p in base.glob('o_*.sh')):
  before=(base/name).read_text();after=(build/name).read_text();want=before
  replacements={oldcfg['token']:newcfg['token'],B.sha((base/'1.tgz').read_bytes()):B.sha(raw),
    oldcfg['export_binding']['object']:pin['object'],
    B.done_path(oldcfg['export_binding']['run'],200):pin['done'],
    "b['run']=='673bc60f' and b['step']==200 and b['member_directory']=='m200'":
      "b['run']==%r and b['step']==%d and b['member_directory']==%r"%(pin['run'],pin['step'],pin['member_directory']),
    "int(f[1])==21583032320 and f[2]=='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'":
      'int(f[1])==%d and f[2]==%r'%(pin['archive_bytes'],pin['archive_sha256']),
    '--lineage SFT --step 200':'--lineage %s --step %d'%(pin['lineage'],pin['step']),
    '= 5395758080':'= %d'%pin['part_bytes']}
  for a,b in replacements.items():want=want.replace(a,b)
  if name.startswith('o_pullfill'):
   want=want.replace('I=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs\n','')
   copies=''.join('cp "%s" "$E/%s"\n'%(pin['prep_paths'][key],dest) for key,dest in [('config','7'),('receipt','8'),('data_receipt','9')])
   if name=='o_pullfill.sh':
    want=re.sub(r'cp "\$I/[^\n]+\ncp "\$I/[^\n]+\ncp "\$I/[^\n]+\n',lambda _:copies,want)
   else:want=want.replace('test -f "$A/0.tgz"\n','test -f "$A/0.tgz"\ncp "$DONE" "$E/5"\n'+copies)
  assert want==after,'Unexpected script change: '+name
  scripts[name]=(before,after)
 for prefix,ad,bd in [('package/',old,new),('src/',op,np)]:
  for n in ad:
   if n.endswith('.sh'):scripts[prefix+n]=(ad[n].decode(),bd[n].decode())
 helpers={('package/'+n):v for n,v in new.items() if n.endswith('.py')}
 helpers.update({'src/'+n:v for n,v in np.items() if n=='8.py' or (n.startswith('orchard_h10/') and n.endswith('.py'))})
 helpers.update({'bundle/'+n:v for n,v in B.bundle_of(new['BATCH.sh']).items() if n.endswith('.py')})
 batch_code=re.findall(r"<<'A'\n(.*?)\nA\n",new['BATCH.sh'].decode(),re.S)
 assert len(batch_code)==1
 helpers['heredoc/BATCH.py']=batch_code[0].encode()
 for n in ('fetch_return.py','unpack_return.py','tower_sequence.py'):helpers[n]=(build/n).read_bytes()
 embedded_shells=0
 for n,(before,after) in sorted(scripts.items()):
  lines.append('\nSCRIPT %s: %s\n'%(n,'IDENTICAL (empty unified diff)' if before==after else 'unified diff follows'))
  lines.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='b200/'+n,tofile='r400/'+n))
  subprocess.run(['bash','-n'],input=after,text=True,check=True)
  for i,code in enumerate(re.findall(r"<<'SHELLCODE'\n(.*?)\nSHELLCODE\n",after,re.S)):
   subprocess.run(['bash','-n'],input=code,text=True,check=True);embedded_shells+=1
  for i,code in enumerate(re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE\n",after,re.S)):
   helpers['heredoc/'+n+'/'+str(i)+'.py']=code.encode()
 paths=[]
 for n,v in sorted(helpers.items()):
  path=work/n;B.put(path,v);paths.append(str(path))
 code='import py_compile,sys\nassert sys.version_info[:2]==(3,6)\nfor p in sys.argv[1:]:py_compile.compile(p,cfile=p+".pyc",doraise=True)\nprint(sys.version.split()[0])'
 result=subprocess.run(['/usr/bin/python3','-I','-s','-B','-c',code]+paths,capture_output=True,text=True,check=True)
 evidence=dict(passed=True,delivery_sha256=B.sha(raw),scripts=len(scripts),embedded_shells=embedded_shells,
               python=result.stdout.strip(),py_compile_helpers=len(helpers),helper_names=sorted(helpers),script_names=sorted(scripts),plan_changes=plan_changes)
 lines.append('\nVALIDATION '+json.dumps(evidence,sort_keys=True)+'\n')
 Path(diff_output).write_text(''.join(lines));B.put(build/'VALIDATION.json',B.jbytes(evidence))
 print(json.dumps(evidence,sort_keys=True))

if __name__=='__main__':main(*sys.argv[1:])
