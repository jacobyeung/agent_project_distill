#!/bin/bash
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 R2_FAST_CENSUS=1
export R2_TREE=/scratch/jjyeung/orch_n30/review_tree9/pkg/work/tree_r1 R2_LANE_ROOT=/scratch/jjyeung/orch_n30/review_tree9/pkg R2_ALL_TESTS=0 R2_PACKAGE_MEMBERS=
ulimit -f 204800
cd /scratch/jjyeung/orch_n30/review_tree9/pkg
PY="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
R2_SUITE_GROUP=r2 timeout 2400 $PY /scratch/jjyeung/orch_n30/review_tree9/pkg/work/build9/test_runner.py /scratch/jjyeung/orch_n30/review_tree9/pkg/work/rv_suite/r2 > /scratch/jjyeung/orch_n30/review_tree9/suite/r2.log 2>&1; echo r2 rc=$? >> /scratch/jjyeung/orch_n30/review_tree9/suite/done.txt
R2_ALL_TESTS=1 R2_SUITE_GROUP=generator timeout 2400 $PY /scratch/jjyeung/orch_n30/review_tree9/pkg/work/build9/test_runner.py /scratch/jjyeung/orch_n30/review_tree9/pkg/work/rv_suite/generator > /scratch/jjyeung/orch_n30/review_tree9/suite/generator.log 2>&1; echo generator rc=$? >> /scratch/jjyeung/orch_n30/review_tree9/suite/done.txt
R2_SUITE_GROUP= timeout 2400 $PY /scratch/jjyeung/orch_n30/review_tree9/pkg/work/build9/test_runner.py /scratch/jjyeung/orch_n30/review_tree9/pkg/work/rv_suite/legacy_sel tests.test_e2e_shared_rows tests.test_provisional_pipeline tests.test_clean_r1313 tests.test_live_adapter_r3 tests.test_gf1_cache > /scratch/jjyeung/orch_n30/review_tree9/suite/legacy.log 2>&1; echo legacy rc=$? >> /scratch/jjyeung/orch_n30/review_tree9/suite/done.txt
