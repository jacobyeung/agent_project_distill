export TZ=UTC; date -u +%FT%TZ
squeue -j 172660 --start -o '%i %T %S %R' 2>&1
for n in 0 1 2 3 4; do echo "community-$n $(scontrol show node orchard-community-$n | grep -oE 'AllocTRES=[^ ]*' | grep -oE 'gres/gpu=[0-9]+')"; done
squeue -w orchard-community-0 -o '%i %u %P %j %b %M' | head
