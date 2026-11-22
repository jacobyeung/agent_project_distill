#!/bin/bash
# Each case in its own user+mount namespace with /tmp bound to a fresh lane folder.
set -u
T=/scratch/jjyeung/orch_n30/lever7/nfa/fix2/t
PY=/scratch/jjyeung/envs/p1cpu/bin/python
run() { # name job package mode
  mkdir -p "$T/ns/$1"
  env -i PATH=/usr/bin:/bin HOME=/home/jjyeung USER=jjyeung SLURM_JOB_ID="$2" CUDA_VISIBLE_DEVICES= \
    unshare -r -m bash -c "umask 077; mount --bind $T/ns/$1 /tmp && exec $PY -I -s -B $T/rehearse_root.py $3/a/5.py $3 $T/res_$1 $4" \
    > "$T/out_$1.json" 2> "$T/err_$1.txt"
  echo "$1 exit=$?"
}
mkdir -p "$T/ns"
run old174294_b 174294 "$T/P_old" old_tripped
run new174294_b 174294 "$T/P_new" new
run new9999999_b 9999999 "$T/P_new" new
run new100000_b 100000 "$T/P_new" new
run newexists_b 174294 "$T/P_new" exists
