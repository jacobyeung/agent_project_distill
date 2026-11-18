export TZ=UTC
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
squeue -u jjyeung -n a15_cot_ap5ee9da63 -h | grep -q . && { echo "already queued"; exit 3; }
bash $B/s.sh 2>&1 | grep -v ': OK$'
echo s_rc=${PIPESTATUS[0]}
squeue -u jjyeung -n a15_cot_ap5ee9da63 -o '%i %j %P %T %R'
