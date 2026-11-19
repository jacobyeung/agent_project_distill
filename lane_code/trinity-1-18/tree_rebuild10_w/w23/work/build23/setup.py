from pathlib import Path
import json,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build23';B=L/'work/build21'
# All generated evidence and writes stay inside this workspace.
s=(L.parent/'w22/work/build22/lookahead.py').read_text()
s=s.replace("D=L/'work/build22'", "D=L/'work/build23'")
s=s.replace("milestone=600", "milestone=400")
s=s.replace("LOOKAHEAD_KITQ.json", "LOOKAHEAD_BEFORE.json")
(D/'lookahead_before.py').write_text(s)
(D/'START.json').write_text(json.dumps(dict(workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file()),tree=json.loads((L/'out/TREE_SEAL.json').read_text()))))
# Package inputs use old absolute paths. Redirect their authenticated bytes on reads,
# while fixture producers and package paths use this workspace explicitly.
for name in ('config.json','kit_config.json','mix.json','room_audit.json'):
    shutil.copyfile(B/'inputs'/name,L/'attic/build23'/name)
