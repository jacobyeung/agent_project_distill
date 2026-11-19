#!/bin/bash
export READ_INPUT_SRC=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src
export READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts
exec bash /scratch/jjyeung/orch_n30/so_read/work/cpu.sh "$@"
