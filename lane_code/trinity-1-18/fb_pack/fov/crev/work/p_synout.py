"""Check (without writing) whether build3 fresh_output accepts a synthetic run at the real run's output path."""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('sf3', '/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.core.fresh = lambda p: ('WOULD_CREATE', str(p))
for synthetic in [(1.0, 1.0), None]:
    try:
        print('synthetic' if synthetic else 'real', m.fresh_output(m.ROOT / 'out/fov544_score', synthetic))
    except m.core.Refusal as exc:
        print('REFUSED', exc)
