J=173964; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/$J; LOG=$O/j2.log
echo "--date $(date -u +%H:%M:%SZ)"; TZ=UTC sacct -j $J -X -n -o JobID,State,Start,Elapsed,NodeList 2>/dev/null
echo "--O"; ls -la --time-style=+%H:%M:%S $O 2>&1 | tail -40
echo "--live"; ls -la --time-style=+%H:%M:%S $O/live 2>&1 | tail -30
echo "--ok"; for f in r.log q.log; do echo "$f: $(grep -c '{"ok": true}' $O/$f 2>/dev/null) ok / $(grep -c '{"ok": false}' $O/$f 2>/dev/null) false"; grep -E '^\{"ok"' $O/$f 2>/dev/null | tail -1; done
echo "--epsha"; grep -E 'receipt.json sha256=|materialization.json sha256=' $LOG 2>/dev/null | tail -8
echo "--q0"; python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print({k:d.get(k) for k in ('status','refusal','init_milestone','config')})" $O/q0.json 2>&1 | cut -c1-400
echo "--j7"; ls -la --time-style=+%H:%M:%S $O/j7 2>&1 | tail -25; test -s $O/j7/j7.json && sha256sum $O/j7/j7.json
echo "--sel"; for f in routing_selection.json db_bytes.json; do test -s $O/$f && sha256sum $O/$f || echo "$f missing"; done
echo "--census"; for i in 0 1 2 3 4; do f=$O/live/c$i.json; test -s $f && echo "c$i $(stat -c %s $f) B protected_keys=$(grep -o '"protected[a-z_]*"' $f | sort | uniq -c | tr '\n' ' ')" || echo "c$i missing"; done
echo "--logtail"; tail -6 $LOG 2>/dev/null | cut -c1-300
echo "--steps"; tail -4 $O/q.steps 2>/dev/null | cut -c1-200
echo "--node"; timeout 100 srun --overlap --jobid $J -n1 -N1 timeout 80 nice -n 19 bash -s <<'IN' 2>&1 | head -60
N=/tmp/q_22c714e1_$SLURM_JOB_ID; [[ -d $N ]] || N=${SLURM_TMPDIR:-/tmp}/q_22c714e1_$SLURM_JOB_ID; ls --time-style=+%H:%M:%S -la $N | tail -25
echo "== node j2.log epsha"; grep -E 'receipt.json sha256=|materialization.json sha256=|work exit' $N/j2.log 2>/dev/null | tail -8; tail -3 $N/j2.log | cut -c1-250; tail -2 $N/j2.retry.log 2>/dev/null
for f in q.log dr/q.log; do echo "== $f"; grep -E '^\{"ok"' $N/$f 2>/dev/null | tail -1; tail -2 $N/$f 2>/dev/null | cut -c1-250; done
test -f $N/p/q/RESULT.json && head -c 300 $N/p/q/RESULT.json
tail -3 $N/$SLURM_JOB_ID.steps 2>/dev/null | cut -c1-200
echo "== newest under dr"; find $N/dr -maxdepth 4 -newermt '6 minutes ago' -printf '%TH:%TM:%TS %s %P\n' 2>/dev/null | sort | tail -6 | cut -c1-200
IN
