import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
for name in ('q','n','n_go'):
 k=kit(name)
 for f in ('ep.py','ep.sh'):replace(k/'b'/f,(D/f).read_bytes(),0o755 if f.endswith('.sh') else 0o644)
 p=k/'job.sh';s=p.read_text()
 if name=='q':
  needle='python3 -B -I -s -B "$ROOT/b/x.py" "$ROOT" "$R" "$N" 2>&1 | python3 -B -I -s -B "$ROOT/b/l.py" "$ROOT"'
  assert needle in s
  s=s.replace(needle,'source "$ROOT/b/ep.sh"\nsetsid bash -c \'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"\' bash "$ROOT" "$R" "$N" &\nTK_WORK_PID=$!\nwait "$TK_WORK_PID"')
  replace(p,s,0o755)
 else:
  p=k/'b/pc.sh';s=p.read_text();needle='    exit "$status"'
  s=s.replace(needle,'    python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" "$status" || true\n'+needle)
  replace(p,s,0o755)
 p=k/'k/j.json';s=base64.b64decode(json.loads(p.read_text())['payload']).decode()
 # Every mode receives an exit trap before staging. This shell runs outside bwrap.
 trap="""tk_evidence_exit() {
    local status="$1"
    trap - EXIT TERM USR1
    /usr/bin/python3 -B -I -s "$Q_KIT/b/ep.py" "$Q_KIT" "$Q_ROOT" "${SLURM_JOB_ID:?}" "$status" || true
    exit "$status"
}
trap 'tk_evidence_exit $?' EXIT
trap 'exit 143' TERM
trap 'exit 138' USR1
"""
 s=s.replace('set -euo pipefail\n','set -euo pipefail\n'+trap,1)
 s=s.replace('if [[ -n "${SLURM_JOB_ID:-}" && -d "$HM/o" ]]; then printf \'%s\\n\' "$line" >> "$HM/o/$SLURM_JOB_ID.steps" 2>/dev/null || true; fi','if [[ -n "${SLURM_JOB_ID:-}" ]]; then printf \'%s\\n\' "$line" >> "$Q_ROOT/$SLURM_JOB_ID.steps"; fi')
 cap(k,'k/j.json',s.encode());print(name,reseal(k))
