date -u; uptime
for t in filter move; do echo "== $t"; tail -c 400 /scratch/jjyeung/orch_n30/sm_$t/codex.log; echo; tail -4 /scratch/jjyeung/orch_n30/sm_$t/work/STATUS.md 2>/dev/null; ls /scratch/jjyeung/orch_n30/sm_$t/out; head -3 /scratch/jjyeung/orch_n30/sm_$t/out/REPORT.md 2>/dev/null | cut -c1-300; done
