export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"; squeue -p advanced -h -o "%u %T %b" | sort | uniq -c | head; sinfo -p preempt -h -o "%P %a %D %C" | head -3
cd $X; for K in q n qd; do echo "$K $(sha256sum $K/SHA256SUMS.txt | cut -c1-16)"; done; ls; ls rcj 2>/dev/null
