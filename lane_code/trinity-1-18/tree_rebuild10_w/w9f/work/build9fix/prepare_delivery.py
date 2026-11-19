from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
p=B/'make_delivery.py';s=p.read_text()
s=s.replace("'work/build9fix/kits',", "'work/build9fix/kits','work/build9fix/inputs',")
s=s.replace("size=sum(p.stat().st_size for p in members)", "members.extend(p for p in B.iterdir() if p.is_file() and p.suffix in ('.py','.sh'))\nmembers=list(dict.fromkeys(members))\nsize=sum(p.stat().st_size for p in members)")
p.write_text(s)
p=B/'package.py';s=p.read_text()
start=s.index("if (root/'work/build9fix/kits/a0').is_dir()")
end=s.index("(out/'KIT_TESTS.json')",start)
s=s[:start]+'''from launch_r1.build import verify as verify_r1
kit=root/'work/build9fix/kits/r1'
kit_results.append(dict(kit='r1',sha256=verify_r1(kit),source_revision='sha256:'+digest(source_before)))
'''+s[end:]
p.write_text(s)
# Preserve immutable build-9 reporting inputs before refreshing requested report paths.
for name in ('BUILD9_REPORT.md','TREE_SEAL.json','MIX_A0.json'):
    src=L/'out'/name;dst=B/('INHERITED_'+name)
    if not dst.exists():dst.write_bytes(src.read_bytes())
print('Delivery harness configured for the R1 kit; base receipts retained unchanged.')
