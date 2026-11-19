#!/bin/bash
G=$1; TREE=$2; shift 2
W=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/..
mkdir -p /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/suites
export LANE_TEST_OUTPUT=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G R2_FIXTURES=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/fixtures R2_PROOFS=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G TMPDIR=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G R2_FIXTURES=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/fixtures R2_PROOFS=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G/c HF_HOME=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G/hf TORCH_HOME=/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/tmp/suite_$G/t
ulimit -f 204800
cd $TREE
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys;sys.path.insert(0,'.');import unittest;unittest.main(module=None,argv=['x','-v']+sys.argv[1:])" "$@" > /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/suites/$G.log 2>&1
echo "rc=$?" >> /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/suites/$G.log
