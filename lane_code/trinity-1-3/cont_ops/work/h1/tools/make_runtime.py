from pathlib import Path
import json
from private_paths import CHECK
H=Path(__file__).resolve().parents[1];D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0');tok=json.loads((H/'TOKENS_H1.json').read_text())
s=(D/'jobB/jb.sh').read_text()
assert '3b8f' not in s
s=s[s.index('#!/bin/bash'):]
start=s.index('#SBATCH')
s='#!/bin/bash\n# Conditional four-rank entry; a separate submission approval is required.\n'+s[start:]
for a,b in [('x_f5c353f7','x_'+tok['kit']),('runs/359fcc3c','runs/'+tok['run']),('r/63e57182','r/'+tok['root']),('i_bb09a77d/vt.py','i_'+tok['store']+'/v.py'),('24:00:00','13:00:00'),('TK_JOB_START + 86400','TK_JOB_START + 46800')]:s=s.replace(a,b)
s=s.replace('set -uo pipefail', 'set -uo pipefail\n'+CHECK)
s=s.replace('/tmp/jjyeung/okit_8865619b/runs/', '/tmp/jjyeung/a_17c4ffa4/runs/')
old='mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$RUN" "$RS" "$KH/o"'
new='''# BEGIN directory preflight
NL=/tmp/jjyeung/a_17c4ffa4
private_dir "$KH"
for p in /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS"; do
    [[ ! -e "$p" && ! -L "$p" ]] || private_dir "$p"
done
for p in "$NL/runs"/* "$NL/runs"/.[!.]* "$NL/runs"/..?*; do
    [[ ! -e "$p" && ! -L "$p" ]] && continue
    [[ "${p##*/}" == 17c4ffa4 && -d "$p" && ! -L "$p" ]] || { echo 'foreign run directory; refusing' >&2; exit 3; }
done
mkdir -p -m 700 /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS" "$KH/o" || exit 3
for p in "$NL" "$NL/runs" "$RUN" "$RS"; do private_dir "$p"; done
# END directory preflight'''
assert s.count(old)==1
s=s.replace(old,new)
(H/'runtime/jb.sh').write_text(s);(H/'payload/jb.sh').write_text(s)
