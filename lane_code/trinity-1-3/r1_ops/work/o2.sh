export TZ=UTC; date -u
O=/project/community/jjyeung/okh7
squeue -u $USER -o '%i %j %P %T %M %R' | grep -v jjy_ 
sha256sum $O/x_3fdda0fb/SHA256SUMS.txt
ls -la $O/i_1be16f28/ | head -40
ls -la $O/i_1be16f28/q_6c18a2bf $O/i_1be16f28/q_6c18a2bf/o 2>&1 | head -30
ls $O/x_3fdda0fb/k | head -50
