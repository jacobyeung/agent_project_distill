set -u
P=/project/community/jjyeung/b9ef552934627
ls -la $P | head -40
ls -la $P/a 2>/dev/null | head -40
wc -c $P/BATCH.sh; head -c 1500 $P/BATCH.sh; echo
cat $P/PACKAGE.json 2>/dev/null | head -c 2000; echo
df -h /project | tail -1
TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M %N"
TZ=UTC sacct -j 171253 -X -n -o JobID,State,Elapsed,NodeList,Partition
