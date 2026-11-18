export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d
cd $KH
echo "== SLOT_MISSING"; cat o/171337.SLOT_MISSING; echo
echo "== err"; cat o/171337.err | cut -c1-300
echo "== w.steps"; cat o/171337.w.steps
echo "== steps"; cat o/171337.steps | cut -c1-200
python3 -I -B - "$KH" <<'P'
import sys,os
from pathlib import Path
r=Path(sys.argv[1]); exp=set(l.split('  ',1)[1] for l in (r/'SHA256SUMS.txt').read_text().splitlines())
act={str(p.relative_to(r)) for d in ('b','k') for p in (r/d).rglob('*') if p.is_file()}
act.update(n for n in ('job.sh','job8.sh') if (r/n).is_file())
import time
for n in sorted(act-exp): print('EXTRA',n,os.stat(r/n).st_size,time.strftime('%H:%M:%S',time.gmtime(os.stat(r/n).st_mtime)))
for n in sorted(exp-act): print('MISSING',n)
print('n_expected',len(exp),'n_actual',len(act))
P
ls -la --time-style=+%H:%M:%S $KH $KH/k | head -60
