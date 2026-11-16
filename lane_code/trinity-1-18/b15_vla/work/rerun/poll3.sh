R=/project/community/jjyeung/vla_libero/out/rerun_20261116; tail -3 $R/phase.log | cut -c1-900
T=/project/community/jjyeung/okh7/i_bb09a77d; ls -la $T
cd $T && timeout 120 tar tvf m.tar 2>&1 | head -60
