import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
limits()
prepare_sandbox()
record = command('preflight4', T/'preflight', T/'preflight/project', '2420',
                 [PY, '-I', '-s', '-B', '-c',
                  "import sys; sys.path.insert(0, " + repr(str(TREE)) + "); from student_pilot.carrier_c1_run import identity; from launch_r1.entry import ASSERTIONS; import torch; print(identity({'contract_epoch':False})); print(ASSERTIONS); print(torch.get_num_threads(),torch.get_num_interop_threads())"])
print(record['stdout']); print(record['stderr'])
