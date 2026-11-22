#!/bin/bash
# One GPU attempt on preempt (ANSWER 0032Z): the package's own submit (its argv keeps --no-requeue),
# held at once, moved to preempt and pinned to orchard-community-0..3, then released.
set -euo pipefail
umask 077
P=/scratch/jjyeung/orch_n30/lever7/nfa/fix2/t/osim/P2
test ! -e "$P/a/70.txt"
test ! -e "$P/a/71.txt"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$P" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);h=lambda n:hashlib.sha256((p/n).read_bytes()).hexdigest()
c=json.loads((p/'a/c/CPU.json').read_text());z=json.loads((p/'0.json').read_text());k=json.loads((p/'2.json').read_text())
ok=(c.get('passed') is True and c.get('entry_sequence_passed') is True and c.get('bundle_guard_passed') is True
    and c.get('cpu_reads_passed') is True and c['operator_sha256']==h('a/6.py') and c['payload']==z['payload_sha256']
    and c['plan']==z['plan_sha256'] and c['inputs']==h('a/1.json') and k.get('passed') is True
    and k.get('gpus')==1 and k.get('time')=='02:30:00' and k.get('plan')==z['plan_sha256'])
if not ok:raise SystemExit('E52')
PY
# Only our own jobs count; another project's job may hold general.
q=$(squeue -u jjyeung -h -o '%j' | grep '^a15_cot_ap' || true)
test -z "$q"
pool=$(du -sm /project/community/jjyeung/okh7/ae71c903 | cut -f1)
test "$pool" -le 75
nodes=$(sinfo -h -p preempt -N -o '%N' | sort -u)
keep=$(printf '%s\n' "$nodes" | grep -E '^orchard-community-[0-3]$' | paste -sd, - || true)
test -n "$keep" || { echo 'E90 no orchard-community-0..3 node in preempt' >&2; exit 1; }
ex=$( { printf '%s\n' "$nodes" | grep -vE '^orchard-community-[0-3]$' || true; } | paste -sd, -)
case ",$ex," in *,orchard-community-4,*) ;; *) ex=${ex:+$ex,}orchard-community-4;; esac
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$P" "$ex" <<'PY'
import ast,sys,tarfile
with tarfile.open(sys.argv[1]+'/0.tgz') as t:src=t.extractfile('orchard_h10/common.py').read().decode()
F=[ast.literal_eval(n.value) for n in ast.parse(src).body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='FORBIDDEN'][0]
if any(w in sys.argv[2].lower() for w in F):raise SystemExit('E91 node list is not opaque')
PY
cd "$P"
out=$(A_N=1 A_T=02:30:00 bash SUBMIT.cmd)
job=$(printf '%s\n' "$out" | sed -n 1p); job=${job%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/a/70.txt")
(set -C; printf '%s preempt\n' "$job" > "$P/a/71.txt")
if ! scontrol hold "$job"; then
  # It started on general before the hold: general carries it.
  printf '%s %s general %s\n' "$job" "$pool" "$(squeue -j "$job" -h -o '%P %T' || true)"; exit 0
fi
if scontrol update JobId="$job" Partition=preempt && scontrol update JobId="$job" ExcNodeList="$ex"; then
  part=$(squeue -j "$job" -h -o '%P')
  exc=$(scontrol show job "$job" | tr ' ' '\n' | sed -n 's/^ExcNodeList=//p')
  want=$(printf '%s\n' "$ex" | tr ',' '\n' | sort -u | paste -sd, -)
  have=$(scontrol show hostnames "$exc" 2>/dev/null | sort -u | paste -sd, - || true)
  if [ "$part" != preempt ] || [ "$have" != "$want" ]; then
    echo "E93 $job held: partition $part, exclusion differs; release it for general or cancel it" >&2; exit 1
  fi
  scontrol release "$job"
  printf '%s %s preempt %s\n' "$job" "$pool" "$keep"
else
  echo "E92 $job held: update refused; release it for general or cancel it" >&2; exit 1
fi
