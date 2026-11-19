W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; find $W/w24 -maxdepth 4 -name SHA256SUMS.txt -newer $W/w24/out/tree_rebuild_b24i_21c21f01.tar 2>/dev/null | head; 
for f in $(find $W/w24 -maxdepth 4 -name SHA256SUMS.txt -newer $W/w24/out/tree_rebuild_b24i_21c21f01.tar 2>/dev/null | head); do echo "$(sha256sum $f | cut -c1-16) $f"; done
