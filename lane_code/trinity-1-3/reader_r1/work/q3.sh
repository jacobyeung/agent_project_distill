P=/project/community/jjyeung/e09e45fda45db
sacct -j 170854 -n -X -o state,elapsed,exitcode,start,end 2>/dev/null | head -1
cat $P/a/c/CPU.json; echo; cat $P/a/c/MEMORY.json | head -c 1500; echo
tail -c 1500 $P/a/c/1.log; echo; grep -c . $P/a/c/0.log; tail -c 600 $P/a/c/0.log
sha256sum $P/a/c/CPU.json
