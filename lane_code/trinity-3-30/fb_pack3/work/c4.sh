F=/scratch/jjyeung/orch_n30/fb_pack; C=$F/combo; cd $C && [ -d X ] || cp -a pkg/work/tree_r1 X; [ -d R ] || cp -a pkg/work/tree_r1 R
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,hashlib,os
seal=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/combo/pkg/out/TREE24L4T_SEAL.json'))
print({k:(v if not isinstance(v,dict) else len(v)) for k,v in seal.items()})
files=seal['files']; want=seal['commit'].split(':')[1]
cands={'json_sorted':json.dumps(files,sort_keys=True).encode(),'json_sorted_compact':json.dumps(files,sort_keys=True,separators=(',',':')).encode(),
 'lines_sha_path':''.join(f'{h}  {p}\n' for p,h in sorted(files.items())).encode(),'lines_path_sha':''.join(f'{p} {h}\n' for p,h in sorted(files.items())).encode(),
 'lines_path_tab':''.join(f'{p}\t{h}\n' for p,h in sorted(files.items())).encode()}
for k,b in cands.items(): print(k, hashlib.sha256(b).hexdigest()==want)
P
for p in patchA2/out/PATCH_A2.patch donor3/out/PATCH_DONOR3.patch camform2/out/PATCH_CAMFORM2_ON_A2.patch; do echo "== $p"; (cd $C/R && patch -p1 --fuzz=0 --dry-run < $F/$p | tail -15); done
