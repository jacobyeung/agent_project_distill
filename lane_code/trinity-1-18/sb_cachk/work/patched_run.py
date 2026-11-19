from pathlib import Path
import sys,importlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit_v2'))
import mc_common as C
C.ROOT=ROOT
C.OUT=ROOT/'work/patched/out/v2'
C.POPULATION=C.OUT/'POPULATION.json'
C.BARS_AMENDMENT=C.OUT/'BARS_AMENDMENT.json'
C.status=lambda text: print(text)
name=sys.argv.pop(1);sys.argv[0]=name+'.py'
module=importlib.import_module(name)
if name=='mc_summary':getattr(module,sys.argv[1])(*sys.argv[2:])
else:
 result=module.main()
 if isinstance(result,int):sys.exit(result)
