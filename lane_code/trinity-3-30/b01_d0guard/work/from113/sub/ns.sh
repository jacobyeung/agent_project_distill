#!/bin/bash
# run a command in the launcher namespace: logical milestone = code_c8r.tar, tree at its logical root
L=/scratch/jjyeung/orch_n30/native_r2
exec /usr/bin/bwrap --unshare-net --ro-bind /usr /usr --ro-bind /etc /etc --ro-bind /bin /bin --ro-bind /sbin /sbin --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --ro-bind /dev/shm /dev/shm --tmpfs /tmp --tmpfs /scratch \
  --bind $L $L --ro-bind $L/sub/code/sj/orch_cd/evalx /scratch/jjyeung/orch_cd/evalx \
  --ro-bind $L/work/tree /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872 --ro-bind /dev/shm/jjyeung/g13/assets_v1/envs/vllm /scratch/jjyeung/envs/vllm \
  --setenv PYTHONPATH $L/work/np226 --chdir $L/sub "$@"
