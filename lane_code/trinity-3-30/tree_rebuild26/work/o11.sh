export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
ls -la $X/n_s/sess_174085.json; sha256sum $X/n_s/sess_174085.json | cut -c1-16
squeue -j 174085 -h -o "%i %T %r" | grep -q JobHeldUser && scontrol release 174085; sleep 5
squeue -j 174085 -h -o "%i %P %j %T %r %S"; squeue -j 174085 --start -h -o "%i %T %S %r" 2>&1 | head -3
