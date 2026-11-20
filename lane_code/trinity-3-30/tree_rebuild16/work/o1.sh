export TZ=UTC; date -u +%TZ; O=/project/community/jjyeung/okh7
ls -la $O/x_ee227714/runs/6ed2c7aa/ 2>&1 | head; ls -la $O/x_ee227714/runs/6ed2c7aa/inputs/ 2>&1 | head
P=$(ls -d $O/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7* 2>/dev/null | head -1); echo P=$P; ls -la $P 2>&1 | head -30; ls -la $P/routing 2>&1 | head
ls -la $O/h_6ed2c7aa/ 2>&1 | head -20
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
