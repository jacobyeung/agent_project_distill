#!/bin/bash
# n_ops10: mint (step 1) or install (step 2) the launch job's 112 sessions from the final kit's k/y.json (9ce25396; armed n_go keeps y.json).
# usage: sess2.sh mint JOB   |   sess2.sh install JOB   (install: waits for a new watcher line in mon/hist.txt, then 62 s)
set -euo pipefail
M=$1; J=${2:?job}; Y=/scratch/jjyeung/orch_n30/n_ops9/work/gcs/y_24m4z10.json
T=/scratch/jjyeung/orch_n30/n_ops8/work/gcs/sess_job.sh; H=/scratch/jjyeung/orch_n30/n_ops1/work/mon/hist.txt
[[ $(sha256sum $Y | cut -c1-64) == 9ce253964ef8d060ae99be248dab4d743035ef61fd49ee3a5b9642f543a434c2 ]] || { echo "REFUSED: y.json sha"; exit 3; }
[[ ! -s /scratch/jjyeung/orch_n30/n_ops1/work/mon/hk.log ]] || { echo "REFUSED: hk.log not empty"; exit 3; }
case $M in
 mint) bash $T $J mint "" $Y ;;
 install) n0=$(wc -l < $H); for i in $(seq 1 40); do sleep 5; [[ $(wc -l < $H) -gt $n0 ]] && break; done; sleep 62; bash $T $J install "" $Y ;;
 *) echo usage; exit 2;;
esac
