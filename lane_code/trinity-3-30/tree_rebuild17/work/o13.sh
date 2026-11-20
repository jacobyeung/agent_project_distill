P=/project/community/jjyeung/okh7/x_ee227714; date -u +%TZ; ls $P; ls $P/k 2>/dev/null | head -40; for f in $P/k/pool_selection_eac5f9f0.json $P/pool_selection_eac5f9f0.json; do test -f $f && sha256sum $f && ls -la $f; done
ls /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa 2>/dev/null | head; ls /project/community/jjyeung/distill/okit/in 2>/dev/null | head -30
