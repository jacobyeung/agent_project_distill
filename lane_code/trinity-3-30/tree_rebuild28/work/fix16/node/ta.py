"""Test launcher (fix16): runs the candidate b/a.py against the installed, sealed kit.
argv: <candidate folder> <installed kit> <mode> <root> <request>
Test-only differences from running the candidate as the kit's own b/a.py:
 1. a.py's kit folder is the installed kit (its seal and k/ files), not the candidate folder;
 2. the candidate b/pf.py is loaded as module pf, reading k/p.json of the installed kit;
 3. one line is printed when the tree's selection check returns;
 4. the walk stops where the proof would open a device: production_proof.forward raises A15_STOP_BEFORE_FORWARD."""
import importlib.util, json, sys
from pathlib import Path
cand, kit = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
source = (cand / 'b/a.py').read_text()
edits = (
    ("kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')",
     "kit=Path(%r);control=read(kit/'k/a.json')" % str(kit)),
    ("host_entry.check_host_selection = guarded_selection",
     "host_entry.check_host_selection = _a15_selection(guarded_selection)"),
    ("    r=run(request,root/'q',stage=stage)",
     "    proof_module.forward=_a15_stop;r=run(request,root/'q',stage=stage)"),
)
for old, new in edits:
    if source.count(old) != 1:
        raise SystemExit('launcher edit does not apply: ' + old)
    source = source.replace(old, new)
spec = importlib.util.spec_from_file_location('pf', cand / 'b/pf.py')
pf = importlib.util.module_from_spec(spec); sys.modules['pf'] = pf; spec.loader.exec_module(pf)
pf.__file__ = str(kit / 'b/pf.py')
def _a15_selection(inner):
    def checked(cfg, directory, request, result, *, record=False):
        value = inner(cfg, directory, request, result, record=record)
        print(json.dumps({'A15_SELECTION': 'PASS', 'root': str(directory), 'regenerated_sha256': result.get('regenerated_sha256'),
                          'assertion': result['assertions']['routing_selection']}), flush=True)
        return value
    return checked
def _a15_stop(*args, **kwargs):
    raise ValueError('A15_STOP_BEFORE_FORWARD')
sys.argv = [str(cand / 'b/a.py'), *sys.argv[3:]]
scope = {'__name__': '__main__', '__file__': str(cand / 'b/a.py'), '_a15_selection': _a15_selection, '_a15_stop': _a15_stop}
exec(compile(source, str(cand / 'b/a.py'), 'exec'), scope)
