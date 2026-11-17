export TZ=UTC
squeue -j 170525 --start -h 2>&1
sinfo -p advanced -h -o '%P %a %D %t %G' 2>&1 | head
squeue -p advanced -h -t R -o '%u %D %b %M %l' 2>&1 | sort | uniq -c | head
squeue -p advanced -h -t PD -o '%u %r' | sort | uniq -c | head
