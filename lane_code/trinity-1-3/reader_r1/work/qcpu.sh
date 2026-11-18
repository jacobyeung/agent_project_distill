export TZ=UTC; date -u +%FT%TZ
squeue -u $USER -h -o "%i %j %P %T %M %R" | grep -v jjy_
sacct -j 171197,171244,171245 -X -n -o JobID,State,Elapsed
for P in b9ef552934627 f40065df28aa3; do echo "== $P"; tail -3 /project/community/jjyeung/$P/a/4.log 2>/dev/null; tail -3 /project/community/jjyeung/$P/a/4.err 2>/dev/null; ls /project/community/jjyeung/$P/a/c 2>/dev/null; done
