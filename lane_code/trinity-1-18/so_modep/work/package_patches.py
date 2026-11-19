from pathlib import Path
import hashlib,json,difflib,subprocess
L=Path(__file__).resolve().parents[1]
B=Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1')
T=L/'work/tree';O=L/'out/patches'
sets=[('01_fast_paths.diff','S1_PREP_FAST_PATHS',['student_pilot/orchard_paths.py','student_pilot/s1_admission.py','tests/test_modep_fast_paths.py','tests/test_modep_gloo.py']),
      ('02_selected_sql.diff','S1_PREP_SELECT_SQL',['student_pilot/s1_exclusions.py','tests/test_modep_select_sql.py'])]
def sha(raw):return hashlib.sha256(raw).hexdigest()
manifest=dict(base_seal='b262e7a7',base_seal_full='b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',base_package_sha256='fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59',base_tree=str(B),patches=[])
for name,switch,files in sets:
 pieces=[];entries=[]
 for rel in files:
  old=(B/rel).read_bytes() if (B/rel).exists() else b''
  new=(T/rel).read_bytes()
  pieces.append(''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+rel if (B/rel).exists() else '/dev/null',tofile='b/'+rel)))
  entries.append(dict(path=rel,base_sha256=sha(old) if (B/rel).exists() else None,patched_sha256=sha(new),bytes=len(new)))
 raw=''.join(pieces).encode();(O/name).write_bytes(raw)
 manifest['patches'].append(dict(file=name,sha256=sha(raw),bytes=len(raw),switch=switch,enabled_value='1',default='OFF',files=entries,independent=True))
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
