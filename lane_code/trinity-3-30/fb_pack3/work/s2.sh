cd /scratch/jjyeung/orch_n30/sb_own400 && cat -n kit/score_400.py | sed -n 1,112p
P=in/own_400/native/probe; d=$(ls -d $P/*/ | head -1); echo "DIR $d"; ls -la $d; cat $d/PHASE_COMPLETE.json | head -c 800; echo
/scratch/jjyeung/envs/p1cpu/bin/python -c "
import numpy as np,sys;z=np.load('$d/own.npz');print({k:z[k].shape for k in z.files})"
ls in/ | head; ls in/own_544* 2>/dev/null | head -3
