#!/bin/bash
# usage: runpt.sh TREE_DIR TESTPATH... ; runs pytest with tree first on path
L=/scratch/jjyeung/orch_n30/review_contracts/work
T=$1; shift
cd $T
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 XDG_CACHE_HOME=$L/.cache TMPDIR=$OUTD PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 STUDENT_PILOT_TEST_OUTPUT=$OUTD STUDENT_CONVERTER_TEST_OUTPUT=$OUTD LANE_TEST_OUTPUT=$OUTD CLEAN_VSI590K_TEST_ROOT=$OUTD CLEAN_VSI590K_WORKSPACE=$T
exec timeout 3000 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import sys;sys.path[:0]=['$T','$L/btests','$L/mytests'];import pytest
sys.exit(pytest.main(sys.argv[1:]+['-q','-p','no:cacheprovider','--basetemp','$L/tmp/pt_$(basename $OUTD)','--tb=short']))" "$@"
