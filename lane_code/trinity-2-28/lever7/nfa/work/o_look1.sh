set -u
P=/project/community/jjyeung/b9ef552934627
cat $P/a/4.log; echo; cat $P/a/4.txt $P/a/7.txt $P/a/8.txt $P/a/9.txt; echo; cat $P/LEDGER.jsonl | head -c 700; echo
TZ=UTC sacct -j 171244 -X -n -P -o JobID,Partition,AllocCPUS,ReqMem,Timelimit,State 2>&1
