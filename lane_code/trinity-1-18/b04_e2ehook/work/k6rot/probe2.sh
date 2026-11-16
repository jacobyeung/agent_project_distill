cd /scratch/jjyeung/orch_n30 || exit 1
ls rows_rebuild/work | head -30; ls rows_rebuild/out | head
for p in rows_rebuild/work/s0 rows_rebuild/work/s0/pull rows_rebuild/work/s0/pull/m3; do echo "== $p"; ls -la $p 2>&1 | head -15; done
