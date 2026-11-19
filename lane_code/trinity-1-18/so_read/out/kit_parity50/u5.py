import importlib.util,json,sys
from pathlib import Path
p=Path(sys.argv[1]);sys.path.insert(0,str(p.parent))
from a9 import read_wire
spec=importlib.util.spec_from_file_location('u0_probe',p.parent/'u0.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_kit(read_wire(json.loads(p.read_bytes())))
kit.validate_environment(read_wire(json.loads(p.read_bytes())))
import torch
torch.set_num_threads(8)
if not torch.cuda.is_available():raise ValueError('GPU interpreter/environment preflight failed')
print('Environment preflight passed')
