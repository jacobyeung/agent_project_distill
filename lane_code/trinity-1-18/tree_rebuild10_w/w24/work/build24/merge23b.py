from pathlib import Path
import shutil,tarfile,difflib,subprocess,json,hashlib
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=L/'work/tree24';W=L.parent/'w23'
assert (W/'out/BUILD23B_REPORT.md').is_file()
shutil.copytree(L/'work/tree_r1',T)
parts=[];inputs={}
with tarfile.open(W/'out/tree_rebuild_b23_40abf77b.tar') as tar:
 for n in ['launch_r1/build.py','launch_r1/entry.py','launch_r1/production_proof.py','student_pilot/r1_population.py','student_pilot/r1_rooms.py','student_pilot/s1_admission.py']:
  a=tar.extractfile('work/tree_r1/'+n).read().decode();b=(W/'work/tree_r1'/n).read_text()
  parts.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n));inputs[n]=hashlib.sha256(b.encode()).hexdigest()
p=D/'23b_delta.patch';p.write_text(''.join(parts));subprocess.run(['patch','--batch','--forward','-p1','-d',str(T),'-i',str(p)],check=True)
p=T/'student_pilot/r1_coverage.py';s=p.read_text();n=(W/'work/tree_r1/student_pilot/r1_coverage.py').read_text()
a=s.index('def deferred(');b=s.index('def source_names(');na=n.index('# These two catalog');nb=n.index('def source_names(')
s=s[:a]+n[na:nb]+s[b:]
s=s.replace('if deferred(cfg):\n        return ()','if deferred(cfg, sources=sources, read_pins=True):\n        return ()')
a=s.index('    if deferred(cfg):',s.index('def validate_binding'));b=s.index('    sources=',a)
s=s[:a]+'    deferred(cfg, read_pins=True)\n'+s[b:];p.write_text(s)
for p in T.rglob('*'):
 if p.is_file() and p.suffix in ('.orig','.rej'):
  p.rename(L/'attic/build24'/('23b_'+str(p.relative_to(T)).replace('/','_')))
for n in ('MINIMAL_TREE.patch','MINIMAL_MERGE_NOTES.md','BUILD23B_REPORT.md'):
 shutil.copyfile(W/'out'/n,L/'attic/build24'/('23b_'+n))
inputs['student_pilot/r1_coverage.py']=hashlib.sha256(n.encode()).hexdigest() if False else hashlib.sha256((W/'work/tree_r1/student_pilot/r1_coverage.py').read_bytes()).hexdigest()
(D/'MERGE23B.json').write_text(json.dumps(dict(source_report=str(W/'out/BUILD23B_REPORT.md'),source_files=inputs,candidate=str(T),method='Six-file delta plus coverage gate splice preserving build22 FULL camera and wording code.'),indent=2)+'\n')
# All build24 tooling selects the candidate explicitly. Existing native process
# retains its original module objects and sealed source path until it completes.
for name in ('kit.py','tests23.py','tests23b.py','kit_tests.py','native24.py','final_capacity.py'):
 p=D/name;s=p.read_text()
 if 'import os\n' not in s:s='import os\n'+s
 s=s.replace("T=L/'work/tree_r1'","T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'))")
 p.write_text(s)
for name in ('new_tests.py',):
 p=L/'work/build22'/name;s=p.read_text().replace("T=L/'work/tree_r1'","T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'))")
 s=s.replace("suite=unittest.defaultTestLoader", "import student_pilot,launch_r1,tests\nsuite=unittest.defaultTestLoader")
 p.write_text(s)
print('Build23b merged; final tree candidate ready')
