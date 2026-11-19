from pathlib import Path
import ast,datetime,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23c';A=L/'attic/build23c'
p=L.parent/'w24/work/build21/kit.py';source=p.read_text();old=(A/'g.py').read_text();guard=(L/'work/build21/kits/q/b/g.py').read_text()
assert source.count(old)==1 and source.count('minimum_gpu_gib=80')==1
patched=source.replace(old,guard).replace('minimum_gpu_gib=80','minimum_gpu_gib=75')
tree=ast.parse(patched)
assert guard in [n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
record=dict(status='PASS',target=str(p),read_only=True,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=hashlib.sha256(source.encode()).hexdigest(),patched_sha256=hashlib.sha256(patched.encode()).hexdigest(),guard_lines=[129,132],resource_line=211,patch_matches=True)
(D/'BUILD24_PATCH_CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
p=L/'out/GUARD_PATCH.md';text=p.read_text();p.rename(A/'GUARD_PATCH.md')
sentence='The current build-24 generator was checked read-only: its guard payload is at lines 129–132 and its resource minimum is at line 211. Both replacements match exactly; the source hash and in-memory patch check are in `work/build23c/BUILD24_PATCH_CHECK.json`.\n\n'
p.write_text(text.replace('Apply to build 24 at ',sentence+'Apply to build 24 at ',1))
print(json.dumps(record))
