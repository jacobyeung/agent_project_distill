from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";p=D/"patch24e.py";s=p.read_text()
marker=" return reseal(k)"
addition=""" p=k/\x27b/u.py\x27
 if p.exists():
  source=p.read_text()
  source=source.replace("with scope(cfg[\x27r1_training\x27][\x27persisted_files\x27]):", "request=load(r.parent/\x27r.json\x27)\\nfrom launch_r1.production_proof import verify_staging\\nwith scope(request[\x27_paths\x27]),scope(cfg[\x27r1_training\x27][\x27persisted_files\x27]):\\n verify_staging(request)")
  p.write_text(source)
"""
assert s.count(marker)==1;s=s.replace(marker,addition+marker);p.write_text(s)
sys.path.insert(0,str(D));from patch24e import upgrade
for k in (L/"work/build24/kits/q",L/"work/build24/kits/n",L/"out/kit_n_go"):print(k.name,upgrade(k))
# The CPU rehearsal uses r2.json as its request; publish the same authenticated
# request at the production shell location before the native training helper.
p=D/"go/r.json";p.write_bytes((D/"go/r2.json").read_bytes())
