#!/bin/bash
# usage: runpt.sh TREE_DIR TESTDIR TAG TESTPATH... ; pytest with tree first on path
L=/scratch/jjyeung/orch_n30/review_contracts2/work
T=$1; TD=$2; TAG=$3; shift 3
mkdir -p $L/tmp/$TAG
cd $T
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 XDG_CACHE_HOME=$L/.cache TMPDIR=$L/tmp/$TAG PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 STUDENT_PILOT_TEST_OUTPUT=$L/tmp/$TAG STUDENT_CONVERTER_TEST_OUTPUT=$L/tmp/$TAG LANE_TEST_OUTPUT=$L/tmp/$TAG CLEAN_VSI590K_TEST_ROOT=$L/tmp/$TAG CLEAN_VSI590K_WORKSPACE=$T
exec timeout 1500 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import sys;sys.path[:0]=['$T','$TD','$L/mytests'];import pytest
sys.exit(pytest.main(sys.argv[1:]+['-q','-p','no:cacheprovider','--basetemp','$L/tmp/$TAG/pt','--tb=short','-rfE']))" "$@"
