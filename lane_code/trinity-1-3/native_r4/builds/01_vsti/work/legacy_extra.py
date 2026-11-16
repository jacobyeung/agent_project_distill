"""Run inherited pilot metadata checks against a relocated original packet."""
from pathlib import Path
import sys,types,unittest
B=Path(__file__).resolve().parents[1];R=B.parents[1];OLD=R/'from113/builds/02_c8r'
sys.path.append(str(B/'code'))
import paths
paths.install(R/'from113/work/tree')
CORE=B/'code/sj/orch_cd/evalx/work/milestone'
sys.path.extend([str(CORE/'orchard_native'),str(CORE)])
from adapter import dump,pin
source=(OLD/'out/tests/test_core.py').read_text()
source=source.replace("B=Path(__file__).resolve().parents[2]",'B=Path('+repr(str(B))+')')
source=source.replace("W=B.parents[1]/'work'",'W=Path('+repr(str(R/'from113/work'))+')')
source=source.replace("ROOT=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'",'ROOT=Path('+repr(str(CORE))+')')
source=source.replace("sys.path[:0]=[str(ROOT/'orchard_native'),str(ROOT/'native/out2'),str(ROOT)]", "sys.path.extend([str(ROOT/'orchard_native'),str(ROOT/'native/out2'),str(ROOT)])")
fixture=OLD/'work/package_tests/87b9682a34074e14b3cb25e1244dad2d/packet/CONFIG.json'
source=source.replace("W/'p9/metadata/CONFIG.json'",'Path('+repr(str(fixture))+')')
module=types.ModuleType('legacy_extra_core');module.__file__=str(OLD/'out/tests/test_core.py')
exec(compile(source,module.__file__,'exec'),module.__dict__)
names=['test_pilot_report_counts','test_pilot_scheduler_covers_limit']
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(module.Core(n) for n in names))
dump(B/'out/LEGACY_EXTRA.json',dict(run=result.testsRun,passed=result.wasSuccessful(),tests=names,fixture=pin(fixture),source=pin(module.__file__),failures=[(str(t),s) for t,s in result.failures],errors=[(str(t),s) for t,s in result.errors]))
if not result.wasSuccessful():sys.exit(1)
