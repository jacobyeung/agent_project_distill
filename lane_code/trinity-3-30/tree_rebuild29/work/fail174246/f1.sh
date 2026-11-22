export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; L=$X/o/174246/live
sacct -j 174246 -n -P -o JobID,State,ExitCode,Start,End,Elapsed | head -5
echo "== attempt"; cat $L/attempt_174246.json | cut -c1-1500; echo; echo "== ckstop"; cat $L/ckstop.json | cut -c1-800; echo
echo "== X/o/174246"; ls -la --time-style=+%H:%M:%S $X/o/174246 | tail -n +2 | awk '{print $5,$6,$7}' | tr '\n' ';'; echo
echo "== t.log"; cat $L/t.log | tr -c '[:print:]\n' '?' | cut -c1-600
