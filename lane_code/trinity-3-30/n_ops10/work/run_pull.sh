#!/bin/bash
# usage: run_pull.sh JOB test|gate  -> /scratch/jjyeung/orch_n30/n_ops10/work/gate_<JOB>[_test]/ ; one ossh call placed between two watcher calls (mon/sleep 120 for that cycle)
set -u; J=$1; MODE=$2; W=/scratch/jjyeung/orch_n30/n_ops10/work; M=/scratch/jjyeung/orch_n30/n_ops1/work/mon; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
D=$W/gate_$J; [ $MODE = test ] && D=${D}_test; [ -e $D ] && D=$D.$(date -u +%H%M%S); mkdir -p $D
sed -e "s/__J__/$J/g" -e "s/__MODE__/$MODE/g" $W/gate_pull.tpl > $D/pull.sh
old=$(cat $M/sleep); echo 120 > $M/sleep; n0=$(wc -l < $M/hist.txt); until [ $(wc -l < $M/hist.txt) -gt $n0 ]; do sleep 3; done; sleep 50
t0=$(date -u +%FT%TZ); timeout 300 bash $B/tools/ossh.sh 'bash -s' < $D/pull.sh > $D/stream.tgz 2> $D/stderr.txt; rc=$?; echo $old > $M/sleep
grep -E 'IDENTIFICATION|fingerprint|SHA256:' $D/stderr.txt | sed "s/^/$(date -u +%FT%TZ) /" >> $M/hk.log
echo "pull $t0 rc=$rc stream_bytes=$(stat -c %s $D/stream.tgz) sha256=$(sha256sum $D/stream.tgz | cut -c1-16)"; grep -v -E 'IDENTIFICATION|fingerprint' $D/stderr.txt | head -5
mkdir -p $D/x && tar xzf $D/stream.tgz -C $D/x && (cd $D/x && sha256sum -c SHA256SUMS) ; echo "dest=$D/x"; cat $D/x/NOTES 2>/dev/null
