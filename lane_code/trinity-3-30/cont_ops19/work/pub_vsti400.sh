#!/bin/bash
# finish the corpus publish of 6ed2c7aa_s400_vsti_direct_a4525db2f6a (read file verified 7c21aa8a by hand and renamed; index + orphans + INDEX rebuild remain)
C=/scratch/jjyeung/orch_n30/corpus; id=6ed2c7aa_s400_vsti_direct_a4525db2f6a; cd $C/pub
/usr/bin/python3 -s pub.py $C/stage2/index/$id.json index/$id.json corpus_i_$id | tail -2
[ -f $C/stage2/index/$id.orphans.jsonl.gz ] && /usr/bin/python3 -s ../tool/pub.py $C/stage2/index/$id.orphans.jsonl.gz index/$id.orphans.jsonl.gz corpus_o_$id | tail -1
cd $C && python3 tool/ingest_read.py index --out stage2
echo "END $(date -u +%TZ)"
