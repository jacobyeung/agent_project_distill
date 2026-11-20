"""Run build3 score_fov.py in real mode; only the output location check is redirected to crev/work."""
import importlib.util, sys
from pathlib import Path
SRC = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
WORK = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
spec = importlib.util.spec_from_file_location('score_fov_b3', SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fresh_output(path, synthetic):
    old = m.core.ROOT
    try:
        m.core.ROOT = WORK
        return m.core.fresh(Path(path).resolve())
    finally:
        m.core.ROOT = old


m.fresh_output = fresh_output
sys.argv = [str(SRC)] + sys.argv[1:]
sys.exit(m.main())
