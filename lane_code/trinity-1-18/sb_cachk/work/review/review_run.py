"""Run unchanged kit modules with all outputs redirected to the review workspace."""
import importlib
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = Path('/scratch/jjyeung/orch_n30/sb_cachk/work/extract')
sys.path.insert(0, str(SOURCE / 'kit_v2'))
import mc_common as C
C.ROOT = HERE
C.OUT = HERE / 'out/v2'
C.WORK = HERE / 'work/v2'
C.POPULATION = C.OUT/'POPULATION.json'
C.BARS_AMENDMENT = C.OUT/'BARS_AMENDMENT.json'
C.OUT.mkdir(parents=True, exist_ok=True)
C.WORK.mkdir(parents=True, exist_ok=True)
def status(message):
    (HERE / 'STATUS.md').write_text(message + '\n')
C.status = status
C.pin(__file__)
name = sys.argv.pop(1).removesuffix('.py')
sys.argv[0] = str(SOURCE / 'kit_v2' / (name + '.py'))
module = importlib.import_module(name)
if name == 'mc_summary':
    getattr(module, sys.argv[1])(*sys.argv[2:])
else:
    result = module.main()
    if isinstance(result, int):
        sys.exit(result)
