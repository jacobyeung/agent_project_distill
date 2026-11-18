export TZ=UTC
for n in 0 1 2 3 4; do printf 'orchard-community-%s ' $n; scontrol show node orchard-community-$n | grep -oE 'AllocTRES=[^ ]*' ; done
sinfo -h -o '%P|%a|%D|%n' | sort -u | head -20
squeue -h -o '%i|%u|%P|%T|%b|%N' | awk -F'|' '$4=="RUNNING"' | sort -t'|' -k6 | head -40
