K=/project/community/jjyeung/okh7/x_07ca49df
ls $K; echo ==u; ls $K/u 2>&1 | head; ls $K/u/eb3429c5 2>&1 | head -30
echo ==k; ls $K/k | grep -v '^pool_\|^remove_' | head -60
