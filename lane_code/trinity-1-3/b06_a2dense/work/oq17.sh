export TZ=UTC; date -u +%FT%TZ
squeue -j 170320 -h -o '%i %T' 2>&1
echo "-- ours on general"; squeue -u jjyeung -p general -h -o '%i %j %T %S %r' 2>&1
echo "-- all general pending (top 10)"; squeue -p general -h -t PD -o '%i %u %j %r' 2>&1 | head -10
