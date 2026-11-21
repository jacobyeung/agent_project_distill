export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=174085
echo "$(date -u +%TZ) $(squeue -j $J -h -o '%T %r %S %N' 2>&1) start_est=$(squeue -j $J --start -h -o '%S' 2>&1)"
