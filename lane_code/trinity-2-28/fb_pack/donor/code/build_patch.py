from pathlib import Path
import hashlib,json,difflib
W=Path(__file__).resolve().parents[1]; B=W/'work/base';N=W/'work/new'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[line.split('  ',1) for line in (W/'out/TREE_FILES.sha256').read_text().splitlines()]
assert len(rows)==939
for h,p in rows:assert sha(B/p)==h, 'Base changed: '+p
seal=hashlib.sha256(json.dumps({p:h for h,p in rows},sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert seal=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
added=['student_pilot/scale_donor.py','student_pilot/scale_donor_check.py','tests/test_scale_donor.py']
changes=[p for h,p in rows if sha(N/p)!=h]+added
pieces=[];entries=[]
for p in sorted(changes):
 old=(B/p).read_text() if (B/p).exists() else '';new=(N/p).read_text()
 pieces.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+p if old else '/dev/null',tofile='b/'+p))
 entries.append(dict(path=p,base_sha256=sha(B/p) if (B/p).exists() else None,new_sha256=sha(N/p)))
(W/'out/PATCH_DONOR.patch').write_text(''.join(pieces))
forbidden=('r1_routing','r1_coverage','job_env','r2_intake','r2_materialize','runtime','host','distributed')
overlaps=[p for p in changes if any(token in Path(p).stem for token in forbidden)]
result=dict(input_sha256={str(W/'out/TREE_FILES.sha256'):sha(W/'out/TREE_FILES.sha256'),str(W/'out/TREE_SEAL.json'):sha(W/'out/TREE_SEAL.json'),str(Path(__file__).resolve()):sha(Path(__file__))},base_tree_sha256=seal,files=entries,declared_patchA_overlaps=overlaps,overlap_rule='Basenames checked against the task named components; no other lane files inspected.',patch_sha256=sha(W/'out/PATCH_DONOR.patch'),command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/build_patch.py')
result['input_sha256'].update({str(N/e['path']):e['new_sha256'] for e in entries})
(W/'out/FILES_TOUCHED.json').write_text(json.dumps(result,indent=2)+'\n');print('Patch files',len(entries),'seal',seal,'overlaps',overlaps)
