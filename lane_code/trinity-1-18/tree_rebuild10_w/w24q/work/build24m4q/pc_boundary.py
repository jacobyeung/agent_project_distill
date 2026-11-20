import sys,json,importlib.util,os,errno,tempfile
from pathlib import Path
control,tree=sys.argv[1:3];value=json.loads(Path(control).read_bytes())
sys.path[:]=[tree]+value['environment']['paths']
tempfile.tempdir=str(Path(control).parent)
helper=Path(__file__).resolve().parents[2]/'out/rcj/pc.py'
spec=importlib.util.spec_from_file_location('pc_fixture',helper);pc=importlib.util.module_from_spec(spec);spec.loader.exec_module(pc)
pc.worker(control,tree)
for target in value['assets']:
 try:descriptor=os.open(target,os.O_WRONLY)
 except OSError as error:assert error.errno in (errno.EROFS,errno.EACCES),str(error)
 else:os.close(descriptor);raise AssertionError('metadata mount writable')
assert not any(Path(value['model_value']['root']).glob('*.safetensors'))
