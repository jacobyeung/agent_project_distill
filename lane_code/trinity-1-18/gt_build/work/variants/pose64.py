"""VARIANT pose64: run the r180 builder with pose64=True (lift with float64 pose instead of the stored float32 c2w)."""
import runpy, sys
sys.argv = [sys.argv[0]] + sys.argv[1:5] + ['pose64']
runpy.run_path('/scratch/jjyeung/orch_n30/gt_build/work/variants/build_arkit_cr_r180.py', run_name='__main__')
