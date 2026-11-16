export TZ=UTC; date -u +%FT%TZ
squeue -j 170320 -h -o '%i %j %P %T %S %M %l' 2>&1
echo "-- ours on general"; squeue -u jjyeung -p general -h -o '%i %j %T %S %M' 2>&1
echo "-- pending general all jjy"; squeue -u jjyeung -h -t PD -o '%i %j %P %T %r' 2>&1
