"""Verify the real local loader inside each child; no constructor stub."""
import sys,json,importlib.util
from pathlib import Path
control,tree=sys.argv[1:3];v=json.loads(Path(control).read_bytes())
sys.path[:]=[tree]+v['environment']['paths']
logical=Path(v['model_value']['root'])
assert logical.is_dir(),logical
assert (logical/'config.json').is_file()
assert not (logical/'model-00001.safetensors').exists()
assert not (logical/'model.safetensors.index.json').exists()
try:(logical/'readonly_probe').write_text('must refuse')
except OSError:pass
else:raise AssertionError('metadata root is writable')
opened=[]
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and args[0].startswith(str(logical)+'/'):opened.append(args[0])
sys.addaudithook(audit)
helper=Path(__file__).resolve().parents[2]/'out/rcj/pc.py'
s=importlib.util.spec_from_file_location('checked_pc',helper);pc=importlib.util.module_from_spec(s);s.loader.exec_module(pc)
pc.worker(control,tree)
Path(v['output']+'.assets').write_text(json.dumps(dict(opened=sorted(set(opened)),readonly=True,constructed=True,no_loader_stub=True)))
