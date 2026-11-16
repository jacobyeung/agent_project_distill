G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u; uptime
for f in logs/kitcheck.log logs/kit_tests.log logs/cpu_*.log logs/ref_*.log; do echo "== $f"; tail -c 600 $f | tail -4; done
ls harness/out_ref/captures 2>/dev/null | wc -l; ls pred_cpu/*/ 2>/dev/null; tmux list-windows -t b14 2>&1 | cut -c1-40
