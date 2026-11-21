#!/bin/bash
# Run a command in the production-shaped pinned namespace of the local fixture.
R=/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/real_cl2opr5g/j
B=/scratch/jjyeung/orch_n30/lever1_c/r1/tests
exec /usr/bin/bwrap --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/sbin /sbin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
  --ro-bind /etc /etc --ro-bind /opt /opt --ro-bind /run /run --ro-bind /sys /sys \
  --dev-bind /dev /dev --proc /proc --dir /tmp \
  --dir /scratch --bind $R/sj /scratch/jjyeung --bind $R/fsw /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung \
  --dir /lustre --bind $R/m/ap /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap \
  --ro-bind $R/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu \
  --dir /x --ro-bind /scratch/jjyeung/k1/g3t /x/g --ro-bind /scratch/jjyeung/orch_n30/reads228/dl/a2.tar /x/a2.tar \
  --ro-bind $B /x/b --die-with-parent --chdir /tmp \
  env -i PATH=/usr/bin:/bin HOME=/tmp TMPDIR=/tmp OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T CUDA_VISIBLE_DEVICES= \
  /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python -B -I "$@"
