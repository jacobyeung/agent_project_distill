# usage: sed "s/171143/<jobid>/" mon_tpl.sh > mon.sh; timeout 150 bash ossh.sh 'bash -s' < mon.sh
export TZ=UTC; date -u +%FT%TZ
J=171143
squeue -j $J -h -o '%i %j %P %T %M %l %R'; sacct -j $J -n -X -o state,elapsed,exitcode | head -1
timeout 90 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c '
for f in $(find /tmp/a'$J'* -name items.jsonl -path "*journals*" 2>/dev/null); do echo "$(wc -l < $f) $f"; done
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
f=$(ls -t $(find /tmp/a'$J'* -name items.jsonl -path "*journals*" 2>/dev/null) 2>/dev/null | head -1); [ -n "$f" ] && tail -1 $f | python3 -c "import json,sys;r=json.loads(sys.stdin.read());o=r[\"output\"];print(r[\"id\"],r[\"type\"],o.get(\"finish\"),round(r[\"seconds\"],1),[c[\"response\"][:40] for c in o[\"calls\"][\"records\"]][:3])"
find /tmp/a'$J'* -name "*.log" -path "*logs*" -newer /proc/1 2>/dev/null | head -3 | while read l; do echo "== $l"; tail -3 $l; done
' 2>&1 | tail -25
