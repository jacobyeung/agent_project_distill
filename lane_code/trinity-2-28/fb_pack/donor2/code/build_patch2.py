from pathlib import Path
import difflib,hashlib,json,subprocess
W=Path(__file__).resolve().parents[1];B=W/'work/base';N=W/'work/new';D=W.parent/'donor/work/new';O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (O/'TREE_FILES.sha256').read_text().splitlines()}
assert all(sha(B/n)==h for n,h in rows.items())
seal=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert seal.startswith('57a1f14d')
added=['student_pilot/scale_donor.py','student_pilot/scale_donor_check.py','tests/test_scale_donor.py']
changes=sorted([n for n,h in rows.items() if sha(N/n)!=h]+added)
inputs={str(O/'TREE_FILES.sha256'):sha(O/'TREE_FILES.sha256'),str(Path(__file__).resolve()):sha(__file__),str(W.parent/'donor/out/PATCH_DONOR.patch'):sha(W.parent/'donor/out/PATCH_DONOR.patch')}
entries=[]
for name in changes:
 entries.append(dict(path=name,base_sha256=sha(B/name) if (B/name).exists() else None,donor_sha256=sha(D/name),new_sha256=sha(N/name)))
 for root in (B,D,N):
  if (root/name).exists():inputs[str(root/name)]=sha(root/name)
for root,name in ((B,'PATCH_DONOR2.patch'),(D,'PATCH_DONOR2_DELTA.patch')):
 parts=[]
 for p in changes:
  old=(root/p).read_text() if (root/p).exists() else '';new=(N/p).read_text()
  parts.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+p if (root/p).exists() else '/dev/null',tofile='b/'+p))
 (O/name).write_text(''.join(parts))
overlaps={}
for lane in ('patchA2','camform','prior2','pointD'):
 p=W.parent/lane/'out/FILES_TOUCHED.json'
 if not p.exists():overlaps[lane]=dict(status='MISSING',expected_location=str(p));continue
 inputs[str(p)]=sha(p);d=json.loads(p.read_text());other={row['path'] for row in d['files']}
 overlaps[lane]=dict(status='CHECKED',files=sorted(set(changes)&other))
result=dict(input_sha256=inputs,base_tree_sha256=seal,files=entries,delta_files=[e["path"] for e in entries if e["donor_sha256"]!=e["new_sha256"]],overlaps=overlaps,patch_sha256=sha(O/'PATCH_DONOR2.patch'),delta_sha256=sha(O/'PATCH_DONOR2_DELTA.patch'),command='python code/build_patch2.py')
(O/'FILES_TOUCHED.json').write_text(json.dumps(result,indent=2)+'\n')
print('files',len(changes),'overlaps',overlaps)
