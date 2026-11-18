"""Stage 2, one process per rank: the sealed admission with prepare_only=False on CPU, resuming stage 1's prepared state
(same configuration pin, destination, frame roots and 16 threads as b/w.py's mode p call). rank_limit=1 runs one more rank:
exit 75 while ranks remain (the sealed PARTIAL exit), 0 once all four ranks pass, 1 on any failure."""
import json, os, sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / 'b'))
from v import tree, pin
from i import authorize
from d import contract
auth, cfg = authorize(root, 'p', '0')
cur = json.loads((root / 'k/0.json').read_text())
tree({'path': cur['record']['file'], 'sha256': cur['record']['sha256']}, os.environ['TRAINER'], cur['commit'])
sys.path.insert(0, os.environ['TRAINER'])
launch = json.loads((root / 'k/launch.json').read_text())
value = contract(launch, cfg)
from student_pilot.s1_admission import admit
admit(pin(root / launch['config']['file']), Path(value['directory']), value['frame_roots'], threads=16, memory_gib=512, rank_limit=1)
