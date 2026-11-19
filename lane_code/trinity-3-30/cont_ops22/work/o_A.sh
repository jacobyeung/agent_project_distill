K=/project/community/jjyeung/okh7; P=$K/a15_cot_apfadf2291c654b; C=$K/a15_cot_apfdc9b2f878b7e
RET=fadf2291c654b$(printf '%08x' $(cat $P/a/8.txt)); SP=$K/ae71c903; test -d $SP/$RET && ! test -e ${SP}_fetched/$RET && mv $SP/$RET ${SP}_fetched/$RET && echo "moved $RET"
cd $P && sha256sum 0.tgz 0.json BATCH.sh PACKAGE.json a/6.py a/1.json a/f/0.tgz; cd $C && sha256sum 0.tgz 0.json BATCH.sh PACKAGE.json a/6.py a/1.json a/f/0.tgz
sha256sum $K/813f42db/c21a600/READ_PLAN_C600.json; du -sb --exclude=e $P/a $C/a; TZ=UTC sacct -j 173333,173348 -X -n -o JobID,State,Elapsed,NodeList,Partition
