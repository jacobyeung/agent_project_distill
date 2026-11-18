"""Generate the packet-specific rehearsal and read-only preflight drivers."""
from pathlib import Path
from packet_config import PINS,render
W=Path(__file__).resolve().parent
header='''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=@BUNDLE@
KH=@KIT@
printf '%s  %s\\n' '@OUTER@' "$BUN/p.tar" | sha256sum -c --quiet
'''
def put(name,body):
 p=W/name;p.write_text(render(header+body));p.chmod(0o700)
put('rh1.sh', '''[[ $# == 0 ]] || exit 2
cd "$BUN"
exec 9> "$BUN/rehearsal.lock"
flock -n 9 || { echo 'REFUSED: concurrent rehearsal'; exit 4; }
for name in rehearsal.started rehearsal.job.id rehearsal.sbatch.out rehearsal.json a4.json; do
 [[ ! -e "$BUN/$name" && ! -L "$BUN/$name" ]] || { echo "REFUSED: existing $name; inspect, never retry"; exit 4; }
done
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\\n' "$Q"
[[ "$Q" != *a15_cot_ap05b8ac6a* && "$Q" != *a15_cot_ap05b8ac69* ]] || { echo 'REFUSED: C proof or rehearsal queued'; exit 4; }
python3 -I -B - "$KH" <<'TOP'
from pathlib import Path
import sys
k=Path(sys.argv[1])
for entry in k.iterdir():
 if entry.is_symlink() or entry.name not in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'}:raise SystemExit('REFUSED: unexpected kit top-level entry: '+entry.name)
TOP
/usr/bin/python3 -I -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition general --out "$BUN/a4.json"
(set -o noclobber; date -u +%FT%TZ > "$BUN/rehearsal.started")
sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:30:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.out --error=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.err /project/community/jjyeung/okh7/i_7f1589c1/p_05b8ac69.sh /project/community/jjyeung/okh7/i_7f1589c1/a4.json --rehearsal /tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/root > "$BUN/rehearsal.sbatch.out"
python3 -I -B - "$BUN" <<'END'
import json,re,sys
from pathlib import Path
b=Path(sys.argv[1]);s=(b/'rehearsal.sbatch.out').read_text().strip()
m=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',s)
if not m:raise SystemExit('UNCERTAIN: no rehearsal ID; inspect; never resubmit')
job=m[1]
with (b/'rehearsal.job.id').open('x') as f:f.write(job+'\\n')
with (b/'rehearsal.json').open('x') as f:json.dump(dict(job=job,kind='REHEARSAL',partition='general',gpus=0,authority='a4.json',proof=False),f,sort_keys=True)
print('SUBMITTED rehearsal_job='+job+'; never a PASS proof')
END
''')
put('rhf.sh', '''[[ $# == 0 ]] || exit 2
python3 -I -B - "$BUN" "$KH" <<'END'
import json,re,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:]);j=b/'rehearsal.job.id'
assert not j.is_symlink();job=j.read_text().strip();assert re.fullmatch('[1-9][0-9]*',job)
p=k/'o'/(job+'.rehearsal.json')
if not p.exists():print('NOT_YET rehearsal receipt');raise SystemExit(4)
assert not p.is_symlink();d=json.loads(p.read_text())
if d.get('status')=='REHEARSAL_RUNNING':print('NOT_YET rehearsal running');raise SystemExit(4)
assert d.get('status') in ('REHEARSAL_OK','REHEARSAL_FAIL') and d.get('job')==job
assert d.get('rehearsal') is True and d.get('admission_executed') is False
print(json.dumps(d,sort_keys=True,indent=2))
print(d['status']+'; never a PASS proof')
raise SystemExit(0 if d['status']=='REHEARSAL_OK' and d['rc']==0 else 4)
END
''')
put('pre1.sh', '''# Optional argument: login-visible preserved C inputs directory from proof 172180.
[[ $# -le 1 ]] || exit 2
python3 -I -B - "$BUN" "$KH" "${1:-/tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/runs/05b8ac69/inputs}" <<'END'
'''+(W/'preflight_c3.py').read_text()+'''\nEND\n''')

import hashlib
from packet_config import MEMBERS
s=(W/'canary_c3.tpl').read_text()
for token,member in [('GATE_SHA','s.sh'),('SUMS_SHA','sums.txt'),('WRAPPER_SHA','jb.sh')]:s=s.replace('@'+token+'@',hashlib.sha256(MEMBERS[member]).hexdigest())
p=W/'go_submit_canary_08f3a7b2.sh';p.write_text(render(s));p.chmod(0o700)
