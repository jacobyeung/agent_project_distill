#!/bin/bash
set -euo pipefail
umask 077
P=/scratch/jjyeung/orch_n30/lever7/nfa/fix2/t/osim/P
test -e "$P/2.json"
test ! -e "$P/a/c/CPU.json"
q=$(squeue -u jjyeung -p preempt -h -o '%j' | grep '^a15_cot_ap' || true)
test -z "$q"
# Keep the check on orchard-community-0..3: exclude every other preempt node, community-4 as before.
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
s=$(date +%s)
# A failed earlier check is kept, renamed, never removed.
for n in a/c a/4.out a/4.stderr a/6.txt a/11.txt; do if [ -e "$P/$n" ]; then mv "$P/$n" "$P/$n.$s"; fi; done
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=preempt --exclude="$ex" --nodes=1 --ntasks=1 --job-name=a15_cot_apc8b836b4ae536 --cpus-per-task=16 --mem=200G --time=03:00:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/a/4.out" --error="$P/a/4.stderr" --wrap="exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c --seconds 10800")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/a/6.txt")
printf '%s %s\n' "$job" "$keep"
