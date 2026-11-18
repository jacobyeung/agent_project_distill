R=/project/community/jjyeung/okh7/x_3fdda0fb/runs/17c4ffa4
ls -la $R $R/inputs 2>&1 | head -30
for d in $R/inputs/prepare_*; do ls -la $d $d/prepared 2>&1 | head -20; done
