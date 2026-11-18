export TZ=UTC; date -u +%FT%TZ
squeue -u $USER -o '%i %j %P %T %M %l %R %b'
squeue -p advanced -o '%i %u %j %T %M %R %b' | head -20
sinfo -p advanced -o '%n %G %t %C' 2>&1 | head
