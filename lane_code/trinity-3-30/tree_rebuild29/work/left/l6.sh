export TZ=UTC; date -u +%TZ
sinfo -p advanced -h -N -o '%N|%T|%G|%C|%d' | sort -u | head -20
scontrol show partition advanced | grep -E "Nodes=|MaxTime" | head -3
for n in $(sinfo -p advanced -h -N -o '%N' | sort -u); do echo "$n $(scontrol show node $n | grep -oE 'TmpDisk=[0-9]+|Gres=[^ ]+' | tr '\n' ' ')"; done
