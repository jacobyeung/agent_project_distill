import json, sys, time
from pathlib import Path
KIT = Path('/scratch/jjyeung/orch_n30/lever7/nfa/kit'); PAYLOAD = KIT.parent / 'ref/payload'
sys.path[:0] = [str(PAYLOAD / 'b'), str(PAYLOAD / 'tree'), str(PAYLOAD), str(KIT)]
import test_nfa
print([p for p in sys.path][:8])
try:
    import e2e_reader.perception_memo
except Exception as e:
    print('ERR', e, sys.modules.get('e2e_reader'))
