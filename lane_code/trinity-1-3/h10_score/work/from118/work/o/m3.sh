export TZ=UTC
P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029a87
cat $P/EXIT.json; echo; tail -c 1500 $P/JOB.log; echo
sacct -j 170631 -n -o JobID%20,State,Start,End,Elapsed,ExitCode
mkdir -p /project/community/jjyeung/okh7/e6fc152498/ret2 && cd /project/community/jjyeung/okh7/e6fc152498/ret2 && tar xzf $P/result.tar.gz && ls; cat FAILED.json 2>/dev/null | head -c 2000; echo; cat SUMMARY.json 2>/dev/null | head -c 2500; echo; ls logs; tail -c 2500 logs/1.log 2>/dev/null; for f in metadata/journals/*/*/items.jsonl; do echo $f $(wc -l < $f); done
