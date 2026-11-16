#!/bin/bash
# vla_schema_v1 conformance tests owned by vla_libero (T-4 with the hand-eye fit, T-5, T-6) -> $V/out/conformance/. CPU, light.
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/conformance; mkdir -p $O; export VLA_LOG_DIR=$O CUDA_VISIBLE_DEVICES=
( train_env; cd $K && nice -n 10 python -B $K/conformance.py t5 $O/T5.json ) > $O/T5.log 2>&1; echo "T5 $(grep -o '"T5": "[A-Z]*"' $O/T5.json)"
( train_env; cd $K && nice -n 10 python -B $K/conformance.py t6 $DATA/libero_spatial_no_noops_1.0.0_lerobot $K/subsets/libero_spatial_d5_s0.json $O/T6.json ) > $O/T6.log 2>&1; echo "T6 $(grep -o '"T6": "[A-Z]*"' $O/T6.json)"
( sim_env libero; cd $K && nice -n 10 python -B $K/conformance.py t4 $V/data/hdf5 $O/T4.json $O/hand_eye.json ) > $O/T4.log 2>&1; echo "T4 $(grep -o '"T4": "[A-Z]*"' $O/T4.json)"
echo CONFORMANCE_DONE
