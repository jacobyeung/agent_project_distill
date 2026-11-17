export TZ=UTC; date -u +%FT%TZ
squeue -u $USER -p general -h -o '%i %j %T %M %l %R'
squeue -u $USER -h -o '%i %j %P %T' | grep -E "^.* jjy_.* general" || true
