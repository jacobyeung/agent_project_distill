P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029a7c
cat $P/EXIT.json; echo; cat $P/JOB.log; echo; tar tzvf $P/result.tar.gz; mkdir -p /project/community/jjyeung/okh7/e6fc152498/ret1 && tar xzf $P/result.tar.gz -C /project/community/jjyeung/okh7/e6fc152498/ret1 && find /project/community/jjyeung/okh7/e6fc152498/ret1 -type f -exec sh -c 'echo "== $1"; head -c 3000 "$1"; echo' _ {} \;
TZ=UTC squeue -j 170620 -h -o '%i %T %M' ; sacct -j 170620 -n -o JobID%20,State,Elapsed,ExitCode
