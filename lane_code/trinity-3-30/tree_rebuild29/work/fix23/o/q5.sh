export TZ=UTC; date -u +%TZ
squeue -u jjyeung -h -o '%i|%j|%T|%N|%r' | grep c6b14e
sacct -j 174372,174373,174374,174375,174376 -X -n -P -o JobID,State,NodeList,Start,End
for n in 0 1 2 3 4; do echo "== p$n"; cat ~/a15o/f23/p$n.out 2>/dev/null; done
