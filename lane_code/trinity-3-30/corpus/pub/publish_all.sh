cd /scratch/jjyeung/orch_n30/corpus/pub
C=/scratch/jjyeung/orch_n30/corpus
for f in $C/stage2/reads/*.jsonl.gz; do id=$(basename $f .jsonl.gz); /usr/bin/python3 -s pub.py $f reads/$id.jsonl.gz corpus_r_${id//./_} > log_r_$id.txt 2>&1 & sleep 1; done
/usr/bin/python3 -s pub.py $C/stage2/INDEX.jsonl INDEX.jsonl corpus_INDEX > log_INDEX.txt 2>&1 &
/usr/bin/python3 -s pub.py $C/pub/SCHEMA.md SCHEMA.md corpus_SCHEMA > log_SCHEMA.txt 2>&1 &
/usr/bin/python3 -s pub.py $C/pub/HOWTO.md HOWTO.md corpus_HOWTO > log_HOWTO.txt 2>&1 &
/usr/bin/python3 -s pub.py $C/pub/index_20261119T0810Z.tar index/index_20261119T0810Z.tar corpus_indextar > log_indextar.txt 2>&1 &
/usr/bin/python3 -s pub.py $C/pub/tool_20261119T0810Z.tar tool/tool_20261119T0810Z.tar corpus_tooltar > log_tooltar.txt 2>&1 &
wait; echo ALLDONE > ALLDONE
