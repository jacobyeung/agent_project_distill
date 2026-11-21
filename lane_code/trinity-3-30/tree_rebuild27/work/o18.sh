export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
ls -la $X/n_s/sess_174134.json | cut -c1-60; [ "$(sha256sum $X/n/SHA256SUMS.txt | cut -c1-16)" = 9e809db4e0817adf ] && [ "$(sha256sum $X/jn7.sh | cut -c1-16)" = 98edfd9e1f30f4ba ] && scontrol release 174134 && echo RELEASED $(date -u +%TZ)
sleep 8; squeue -j 174134 -h -o "%i %T %M %R %S"
