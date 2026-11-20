"""Run build3 score_fov.py synthetic mode with its test-output root redirected to crev/work (no other change)."""
import importlib.util, sys
from pathlib import Path
SRC = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
WORK = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
spec = importlib.util.spec_from_file_location('score_fov_b3', SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.WORK = WORK
f1, f2, out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [str(SRC), '--synthetic', f1, f2, '--out', str(WORK / out)]
sys.exit(m.main())
