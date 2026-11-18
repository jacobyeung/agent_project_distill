#!/bin/bash
G=$1; TREE=$2; shift 2
W=/scratch/jjyeung/orch_n30/review_treen1/work
mkdir -p $W/n1c3/tmp/suite_$G $W/n1c3/suites
export TMPDIR=$W/n1c3/tmp/suite_$G R2_FIXTURES=$W/n1c3/pkg/fixtures R2_PROOFS=$W/n1c3/tmp/suite_$G OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=$W/n1c3/tmp/suite_$G/c HF_HOME=$W/n1c3/tmp/suite_$G/hf TORCH_HOME=$W/n1c3/tmp/suite_$G/t
ulimit -f 204800
cd $TREE
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys;sys.path.insert(0,'.');import unittest;unittest.main(module=None,argv=['x','-v']+sys.argv[1:])" "$@" > $W/n1c3/suites/$G.log 2>&1
echo "rc=$?" >> $W/n1c3/suites/$G.log
