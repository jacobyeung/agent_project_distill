export TZ=UTC; date -u; squeue -u $USER -o '%i|%j|%P|%T|%M|%l|%R' | grep -v '|PENDING|.*JobHeldUser' ; sinfo -p general -o '%P %a %D %C' 2>&1 | tail -1
