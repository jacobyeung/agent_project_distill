from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
rows=json.loads((B/'PACKET_INPUTS.json').read_text());staging=json.loads((B/'PACKET_STAGING.json').read_text())
for row,actual in zip(rows,staging,strict=True):
    row['source']=str(Path(actual['source']).relative_to(L));row['sha256']=actual['sha256']
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2)+'\n')
p=B/'make_delivery.py';s=p.read_text()
s=s.replace("members=list(dict.fromkeys(members))", "members.extend(L/'out'/name for name in ('MIX_A0.json','MIX_A2.json','MIX_R1.json'))\nmembers=list(dict.fromkeys(members))")
p.write_text(s)
p=B/'package.py';s=p.read_text()
needle="(out/'KIT_TESTS.json')"
i=s.index(needle)
s=s[:i]+"from launch_r2.build import verify as verify_r2\nfor arm in ('a0','a2'):\n    kit_results.append(dict(kit=arm,sha256=verify_r2(root/'work/n1fix3/kits'/arm),source_revision='sha256:'+digest(source_before)))\n"+s[i:]
p.write_text(s)
print('Delivery harness binds the copied packet sources and all three kits.')
