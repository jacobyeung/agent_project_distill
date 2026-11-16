#!/bin/bash
# Stage one backbone and the LIBERO-Spatial data into node-local storage. usage: stage.sh ARM   (ARM = B0 | B1)
# Writes $B/models/Qwen3.5-<ARM> (StarVLA picks its Qwen3.5 wrapper by that substring) and $B/data/lerobot: the four
# suites and their subsets <suite>_<d1|d5|d50>_s0_lerobot (lists in kit/subsets/<suite>_<sub>.json).
# B0 = base Qwen3.5-9B c2022362 from the project HF cache. B1 = base config/tokenizer + the student's full_weights
# (LM and ViT tensors, heads dropped). B1_SRC=tarparts:<glob>:<member prefix> or dir:<full_weights dir>.
set -euo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
B=${B:?node-local root}; ARM=$1; mkdir -p $B/models $B/data/lerobot $B/st
BASE=$V/../cache/hf/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
D=$B/models/Qwen3.5-$ARM
if [ ! -f $D/STAGED.json ]; then
  mkdir -p $D
  if [ $ARM = B0 ]; then
    for f in $BASE/*; do n=$(basename $f); cp -L $f $D/$n; done
  else
    for f in $BASE/*; do n=$(basename $f); case $n in model.safetensors*) ;; *) cp -L $f $D/$n ;; esac; done
    src=${B1_SRC:-tarparts:/project/community/jjyeung/distill/okit/in/cr/m200.p*:ap/f2ad01ad/runs/49becb79/m200}
    case $src in
      tarparts:*) IFS=: read -r _ glob pre <<<"$src"; mkdir -p $B/b1x
        cat $(ls $glob | sort) | tar xf - -C $B/b1x "$pre/full_weights" "$pre/artifact.json"
        mv $B/b1x/$pre/full_weights/* $D/; cp $B/b1x/$pre/artifact.json $D/student_artifact.json ;;
      dir:*) cp -L ${src#dir:}/* $D/ ;;
    esac
    ( train_env; python -B $K/check_b1.py $D $BASE )
  fi
  python3 -c "import json,sys,os; json.dump({'arm':sys.argv[1],'files':sorted(os.listdir(sys.argv[2]))}, open(sys.argv[2]+'/STAGED.json','w'))" $ARM $D
fi
if [ ! -f $B/st/data ]; then  # the four suites' no-noops LeRobot data and every fixed subset (symlink views)
  for su in libero_spatial libero_object libero_goal libero_10; do
    cp -r $DATA/${su}_no_noops_1.0.0_lerobot $B/data/lerobot/
    for s in d1_s0 d5_s0 d50_s0; do
      ( train_env; python -B $K/build_subset.py $B/data/lerobot/${su}_no_noops_1.0.0_lerobot $B/data/lerobot/${su}_${s}_lerobot $K/subsets/${su}_$s.json )
    done
  done
  touch $B/st/data
fi
echo "STAGED $ARM $(du -sh $D | cut -f1) data $(du -sh $B/data/lerobot | cut -f1)"
