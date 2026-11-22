"""Local CPU check through the job's own launcher line: operator main() (rehearsal) -> runner.run ->
Popen(python 5.py NN.json) in metadata/a -> the real worker entry -> launch.main/run_types. No model:
the reader is a stub that fails on type-3 items as SAM 3 does on CPU. argv: operator path, output root."""
import json, sys, time
from pathlib import Path
KIT = Path('/scratch/jjyeung/orch_n30/lever7/nfa/kit'); PAYLOAD = KIT.parent / 'ref/payload'
sys.path[:0] = [str(PAYLOAD / 'b'), str(PAYLOAD / 'tree'), str(PAYLOAD), str(KIT)]
import importlib.util
import test_nfa  # fixtures only
operator, root = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location('op_under_test', operator); OP = importlib.util.module_from_spec(spec); spec.loader.exec_module(OP)
cfg = test_nfa.prepared(root)
art = dict(root=str(root / 'e'), name='x', sha256='0' * 64)
(root / 'artifact.json').write_text(json.dumps(art))
s = json.loads((root / 'settings.json').read_text()); s['artifact_manifest'] = str(root / 'artifact.json')
(root / 'settings.json').write_text(json.dumps(s))
cfg.update(device='cpu', python=str(Path(__file__).with_name('py')), prefix=[])
(root / 'd.json').write_text(json.dumps(dict(action=1, package=str(PAYLOAD), config=cfg, rehearsal=True, end=time.time() + 7200)))
sys.argv = ['7.py', str(root / 'd.json')]
OP.main()
