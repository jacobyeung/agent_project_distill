export TZ=UTC; date -u +%T
squeue -h -u jjyeung -o '%i|%j|%P|%T|%M|%l|%R' | grep -v jjy_
sacct -j 172476 -X -n -P -o JobID,State,ExitCode,Start,End,NodeList
K=/project/community/jjyeung/okh7/x_7f1589c1/o
ls -la --time-style=+%H:%M:%S $K | grep 172476 | awk '{print $5,$6,$7}'
for f in $K/172476.rehearsal.log $K/172476.rehearsal.out $K/172476.rehearsal.err; do [ -f $f ] && { echo "== ${f##*/}"; tail -n 8 $f | cut -c1-300 | sed -E 's#(https?://)[^ "]*#\1REDACTED#g'; }; done
