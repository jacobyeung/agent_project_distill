from pathlib import Path
import hashlib,json,shutil
W=Path(__file__).resolve().parents[1]
S=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
manifest=(W/'out/TREE_FILES.sha256').read_bytes()
rows=[line.split('  ',1) for line in manifest.decode().splitlines()]
errors=[]; actual=[]
for expected,name in rows:
 b=(S/name).read_bytes(); h=hashlib.sha256(b).hexdigest()
 if h!=expected: errors.append(name)
 actual.append((name,h))
# Seal is hash of canonical relative-path map; test known common serializations.
variants={
 'sha_space_path_newline':''.join(f'{h}  {p}\n' for p,h in actual),
 'path_sha_newline':''.join(f'{p}\t{h}\n' for p,h in actual),
 'json_sort':json.dumps(dict(actual),sort_keys=True),
 'json_compact':json.dumps(dict(actual),sort_keys=True,separators=(',',':')),
}
expected_seal='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
seal_methods={k:hashlib.sha256(v.encode()).hexdigest() for k,v in variants.items()}
result={'inputs_sha256':{str(S/p):h for p,h in actual},'manifest_sha256':hashlib.sha256(manifest).hexdigest(),'files':len(actual),'mismatches':errors,'expected_seal':expected_seal,'seal_methods':seal_methods}
assert not errors and len(actual)==939,result
for target in ('base','new'):
 for name,h in actual:
  dest=W/'work'/target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/name,dest)
(W/'out/BASE_VERIFY.json').write_text(json.dumps(result,indent=2)+'\n')
(W/'STATUS.md').write_text('The named build record and seal evidence are retained in out/. All 939 base files match TREE_FILES.sha256; base and new copies are staged locally. The seal serialization is being verified before edits. No implementation has changed.\n')
print({k:v for k,v in result.items() if k!='inputs_sha256'})
