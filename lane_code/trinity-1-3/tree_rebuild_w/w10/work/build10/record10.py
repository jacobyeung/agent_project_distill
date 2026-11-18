from pathlib import Path
import ast,difflib,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
status=B/'STEPS.json'
steps=json.loads(status.read_text()) if status.exists() else {}
if len(sys.argv)>2:steps[sys.argv[1]]=dict(status=sys.argv[2],detail=' '.join(sys.argv[3:]))
status.write_text(json.dumps(steps,indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 10 status\n\nGO=false. Source: STEPS.json.\n\n'+''.join(f'- {k}: {v["status"]}. {v["detail"]}\n' for k,v in steps.items()))
source=L.parent/'work/design/eat1_v7/eat1'
patch=[]
for p in sorted((B/'eat1').rglob('*.py')):
    name=p.relative_to(B/'eat1');old=source/name
    a=old.read_text().splitlines(True) if old.exists() else []
    patch.extend(difflib.unified_diff(a,p.read_text().splitlines(True),fromfile='a/eat1/'+str(name),tofile='b/eat1/'+str(name)))
target=L/'out/EAT1_FIXED_MATH.patch';target.write_text(''.join(patch))
(B/'PATCH.json').write_text(json.dumps(dict(path=str(target.relative_to(L)),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),indent=2)+'\n')
