#!/bin/bash
set -u
W=/scratch/jjyeung/orch_n30/h1_headsft_w; KIT=$W/b6/kit; H=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook/parity_kit/host_restore
export PY=/scratch/jjyeung/envs/vllm/bin/python PY_OVERLAY=$W/pyoverlay
for mode in ${MODES:-forced unforced}; do
  extra=; [ $mode = forced ] && extra=--force-pose-own
  echo "$(date -u +%FT%TZ) start $mode" >> $W/runs/rfb.log
  nice -n 10 bash $KIT/first_batch/real_fixture_batch.sh --config $KIT/configs/h1_1.json --model-manifest $H/model.json --receipt $H/receipt.json --artifact $H/artifact.json --restore $H/RESTORE.json --frames $W/runs/clip_scene0155.json --frames-root /scratch/jjyeung/devs1_frames --ranks 0,1,2,3 --routing-per-rank 2 $extra --threads 48 --output $W/runs/real_$mode${SUF:-} > $W/runs/real_$mode${SUF:-}.log 2>&1
  echo "$(date -u +%FT%TZ) end $mode rc=$?" >> $W/runs/rfb.log
done
