#!/bin/bash
cd /scratch/jjyeung/orch_n30/lever7/gtcd/kit
nice -n 10 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B dense.py --workers 8 > ../logs/dense.out 2> ../logs/dense.err
echo "DENSE_RC=$? $(date -u +%FT%TZ)" > ../logs/rc_dense.txt
