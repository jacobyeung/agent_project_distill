P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ab2
ls -la $P; cat $P/EXIT.json; echo; tail -c 1500 $P/JOB.log; echo; cat $P/RETURN_RECEIPT.json | head -c 1500; echo
sha256sum $P/result.tar.gz
tar tzf $P/result.tar.gz | head -30
TZ=UTC sacct -j 170674 -X -n -o JobID,State,ExitCode,Start,End,Elapsed
