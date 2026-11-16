cd /scratch/jjyeung/orch_n30 2>/dev/null && ls
echo ---readk; ls -la cont_ops/work/d0/readk/ | head -60
echo ---ev; ls -la cont_ops/work/d0/readk/evidence | head -60
echo ---evalx27; ls /scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged 2>&1; ls -la /scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/* 2>&1 | head -30
echo ---rows; ls rows_rebuild/out/rows 2>&1; ls -la rows_rebuild/out/rows/facing 2>&1
echo ---rs; ls -d /scratch/jjyeung/orch_n30/*/out/FLIP_STRATA.json /scratch/jjyeung/*/rs_rows/out/FLIP_STRATA.json /scratch/jjyeung/*/*/rs_rows/out/FLIP_STRATA.json 2>&1 | head
ls -d /scratch/jjyeung/*/back_dir /scratch/jjyeung/*/rs_rows /scratch/jjyeung/orch_n30/*/rs_rows 2>&1 | head
du -sh cont_ops/work/d0/readk 2>&1
