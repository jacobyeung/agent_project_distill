export TZ=UTC; P=/project/community/jjyeung/okh7/ae71c903
for d in $P/*/; do echo "$(basename $d) $(find $d -type f -printf '%s\n' | awk '{s+=$1} END {print s}')"; done
TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %M %R'
TZ=UTC squeue -p general -h -o '%i %u %j %T %M %R' | head -20
