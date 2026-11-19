import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for r in json.loads((L/'work/build7/proofs/audit/RESIZE_AUDIT.json').read_text()):
 if r['portrait_aspect_distorted']!='requires transform-context review':continue
 if r['file'] in ('verifykit/render.py','verifykit/io.py','verifykit/prepare.py','verifykit/model.py','student_pilot/g3t_online.py','student_pilot/grounding_head.py','student_pilot/clean_media.py','student_pilot/reread.py'):continue
 lines=(L/'work/tree_r1'/r['file']).read_text().splitlines();n=r['line']
 print('\n'+r['file']+':'+str(n))
 for i in range(max(0,n-10),min(len(lines),n+4)):print(str(i+1)+': '+lines[i])
