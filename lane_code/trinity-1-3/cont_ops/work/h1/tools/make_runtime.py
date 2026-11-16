from pathlib import Path
import json
H=Path(__file__).resolve().parents[1];D=H.parent/'d0';tok=json.loads((H/'TOKENS_H1.json').read_text())
s=(D/'jobB/jb.sh').read_text()
assert '3b8f' not in s
s=s[s.index('#!/bin/bash'):]
start=s.index('#SBATCH')
s='#!/bin/bash\n# Conditional four-rank entry; a separate submission approval is required.\n'+s[start:]
for a,b in [('x_f5c353f7','x_'+tok['kit']),('runs/359fcc3c','runs/'+tok['run']),('r/63e57182','r/'+tok['root']),('i_bb09a77d/vt.py','i_'+tok['store']+'/v.py'),('24:00:00','13:00:00'),('TK_JOB_START + 86400','TK_JOB_START + 46800')]:s=s.replace(a,b)
(H/'runtime/jb.sh').write_text(s);(H/'payload/jb.sh').write_text(s)
