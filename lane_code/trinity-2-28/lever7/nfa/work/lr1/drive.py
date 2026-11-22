"""Local rehearsal through the job's own launcher line (runner.run -> 5.py entry -> launch.main) with no model:
the worker must die, and its cause must come back encoded."""
import json, sys, time, pathlib
from pathlib import Path
from unittest import mock
KIT = Path('/scratch/jjyeung/orch_n30/lever7/nfa/kit'); PAYLOAD = KIT.parent / 'ref/payload'
sys.path[:0] = [str(PAYLOAD / 'b'), str(PAYLOAD / 'tree'), str(PAYLOAD), str(KIT)]
import test_nfa  # fixtures only
root = Path(sys.argv[1])
cfg = test_nfa.prepared(root)
cfg.update(device='cpu', python=sys.executable, prefix=[])
(root / 'd.json').write_text(json.dumps(dict(action=1, package=str(PAYLOAD), config=cfg, rehearsal=True, end=time.time() + 7200)))
sys.argv = ['7.py', str(root / 'd.json')]
print('E2E', sys.modules.get('e2e_reader'), file=sys.stderr)
with mock.patch.object(pathlib.Path, 'unlink', lambda self, missing_ok=False: None):
    try:
        test_nfa.OP.main()
    except SystemExit:
        m=sys.modules.get('e2e_reader'); print('MOD', m, getattr(m,'__path__',None), file=sys.stderr); raise
