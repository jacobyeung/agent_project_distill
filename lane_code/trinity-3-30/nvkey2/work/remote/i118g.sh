echo "== $(hostname -s) $(date -u +%T)"
cd /tmp/nvk2_excl && cp /scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/b12/work/auth/arkit_3dod_metadata.csv . && sha256sum arkit_3dod_metadata.csv && wc -l arkit_3dod_metadata.csv && head -2 arkit_3dod_metadata.csv
tar cf - -C /tmp nvk2_excl | timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/nvkey1/work/excl && tar xf - -C /scratch/jjyeung/orch_n30/nvkey1/work/excl --strip-components=1 && cd /scratch/jjyeung/orch_n30/nvkey1/work/excl && sha256sum *'
