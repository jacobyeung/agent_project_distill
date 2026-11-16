import subprocess, numpy as np, sys
exec(open('/scratch/jjyeung/orch_n30/gt_rasters/work/proof_arkit/bracket.py').read().replace("print(ID, 'box floor'", "np.save(f'/scratch/jjyeung/orch_n30/gt_rasters/work/proof_arkit/z_{ID}.npy', z); np.save(f'/scratch/jjyeung/orch_n30/gt_rasters/work/proof_arkit/br_{ID}.npy', np.array([lo, hi, floor])); print(ID, 'box floor'"))
