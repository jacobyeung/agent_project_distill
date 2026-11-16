#!/bin/bash
# usage (sbatch): k6job.sh KIND SHARD NSH PAR   (KIND a = ARKit range fetch, v = release-video decode)
# Requeue-safe: a finished part has $OUT/DONE; each attempt works in its own job-id dirs (no cleanup).
set -u
F=/project/community/jjyeung/cp4tk_fr
KIND=$1; SH=$2; NSH=$3; PAR=$4
TAG=${KIND}${SH}n${NSH}
OUT=$F/k6tk/parts/$TAG
J=${SLURM_JOB_ID:-x}_${SLURM_RESTART_COUNT:-0}
echo "start $TAG $(hostname) $(date -u +%FT%TZ) job $J"
[ -f $OUT/DONE ] && { echo "already done"; exit 0; }
L=/tmp/jjy_tk_fr_$J; mkdir -p $L/store $L/media
PY=$F/venv/bin/python
if [ "$KIND" = v ]; then
  $PY $F/bin/k6run.py vlist $SH $NSH > $L/members.txt
  for a in scannet scannetppv2; do
    grep "^$a/" $L/members.txt > $L/m_$a.txt
    if [ -s $L/m_$a.txt ]; then
      t0=$(date +%s); tar -I pigz -xf $F/media/$a.tar.gz -C $L/media -T $L/m_$a.txt; rc=$?
      echo "extracted $a $(wc -l < $L/m_$a.txt) members rc=$rc in $(( $(date +%s) - t0 ))s"
    fi
  done
  echo "media files: $(ls $L/media/*/ | wc -l)"
fi
$PY $F/bin/k6run.py $KIND $SH $NSH $PAR $L || { echo "runner failed"; exit 1; }
echo "decode done $(date -u +%FT%TZ)"
T=$OUT.tmp$J; mkdir -p $T
$PY $F/bin/k6pack.py $L/store $T $TAG 32000 > $L/pack.log || { echo "pack failed"; exit 1; }
cp $L/out.jsonl $T/out.jsonl
if [ -e $OUT ]; then echo "OUT exists; leaving $T"; else mv $T $OUT && touch $OUT/DONE; fi
du -sh $L/store; ls -la $OUT
echo "end $TAG $(date -u +%FT%TZ)"
