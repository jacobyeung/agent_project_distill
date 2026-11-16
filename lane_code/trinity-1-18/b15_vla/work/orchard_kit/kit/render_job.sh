#!/bin/bash
# Render the LIBERO HDF5 demos present in $V/data/hdf5 with ground truth (libero_render.py) into $V/out/renders. CPU, OSMesa.
# usage: render_job.sh [N_DEMOS=2] [STRIDE=4]
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
O=$V/out/renders; mkdir -p $O; export VLA_LOG_DIR=$O
for f in $V/data/hdf5/*/*_demo.hdf5; do
  su=$(basename $(dirname $f))
  ( sim_env libero; cd $K && nice -n 19 python -B $K/libero_render.py $su $f $O ${1:-2} ${2:-4} 256 ) >> $O/render.log 2>&1
done
echo RENDER_JOB_DONE >> $O/render.log
