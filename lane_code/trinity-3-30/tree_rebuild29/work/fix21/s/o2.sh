export TZ=UTC; date -u +%TZ
P=$(ls -d /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_*/config.json | head -1); echo "PCFG $P"; sha256sum "$P"; wc -c "$P"
V=/project/community/jjyeung/okh7/x_22c714e1/o/174246/live/v.json; sha256sum $V; wc -c $V
echo BEGIN_P; gzip -9c "$P" | base64 -w0; echo; echo END_P
echo BEGIN_V; gzip -9c $V | base64 -w0; echo; echo END_V
