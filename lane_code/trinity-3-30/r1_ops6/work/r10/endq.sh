export TZ=UTC; date -u +%FT%TZ
squeue -h -j 172660 -o 'Q %i %T %M %N' 2>&1
sacct -n -j 172660 -X -o JobID,State,ExitCode,Elapsed,End 2>&1 | head -2
R=/project/community/jjyeung/okh7/r/6ed2c7aa; ls -la $R 2>&1 | tail -8
for s in A B; do [[ -f $R/$s.json ]] && { echo "$s.json $(cat $R/$s.json)"; echo "$s.json sha $(sha256sum < $R/$s.json | cut -c1-64)"; }; done
tail -4 /project/community/jjyeung/okh7/x_ee227714/o/172660.w.steps 2>/dev/null
tail -3 /project/community/jjyeung/okh7/x_ee227714/o/172660.steps 2>/dev/null
