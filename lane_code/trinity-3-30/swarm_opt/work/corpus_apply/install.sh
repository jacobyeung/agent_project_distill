#!/bin/bash
# install reviewed corpus tool files (named files only) into corpus/tool; new dated tar in corpus root tool/
set -euo pipefail
S=/scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/tool_new; D=/scratch/jjyeung/orch_n30/corpus/tool
C=/data2/jjyeung/agent_project_data/distill_trace_corpus/tool; TS=$(date -u +%Y%m%dT%H%MZ)
MOD="HOWTO.md SCHEMA.md add_read.sh ingest_read.py"; NEW="prove_kit_alias_ids.py tests/test_kit_alias_proof.py tests/test_new_read_wrapper.py tests/test_review2.py tests/test_review3.py"
pgrep -f "add_read.sh|ingest_read.py" >/dev/null && { echo "ingest running; abort"; exit 3; }
[ "$(sha256sum $D/ingest_read.py | cut -c1-16)" = 97bb63d8a6809977 ] || { echo "preimage ingest_read.py mismatch"; exit 4; }
[ "$(sha256sum $D/add_read.sh | cut -c1-16)" = 4aba9a26e4538f54 ] || { echo "preimage add_read.sh mismatch"; exit 4; }
(cd $D && tar cf /scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/preimage_$TS.tar $MOD)
for f in $MOD $NEW; do cp $S/$f $D/.$(basename $f).new.$$ && mv $D/.$(basename $f).new.$$ $D/$f; done
chmod +x $D/add_read.sh
sha256sum $D/ingest_read.py $D/add_read.sh | cut -c1-16
(cd $D/.. && tar cf /scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/so_tool_$TS.tar tool/HOWTO.md tool/SCHEMA.md tool/corpus_score.py tool/ingest_read.py tool/pub.py tool/add_read.sh tool/prove_kit_alias_ids.py tool/BRIEF_ingest.md tool/BRIEF_fix1.md tool/BRIEF_review.md tool/BRIEF_review2.md tool/tests/__init__.py tool/tests/test_no_leftovers.py tool/tests/test_real_returns.py tool/tests/test_synthetic.py tool/tests/test_kit_alias_proof.py tool/tests/test_new_read_wrapper.py tool/tests/test_review2.py tool/tests/test_review3.py)
ls -l /scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/so_tool_$TS.tar
rsync --bwlimit=4000 /scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/so_tool_$TS.tar $C/tool_$TS.tar
sha256sum /scratch/jjyeung/orch_n30/swarm_opt/work/corpus_apply/so_tool_$TS.tar $C/tool_$TS.tar | cut -c1-16
echo "INSTALLED $TS"
