"""Reviewer read trace of the paths added by this fix, under the GPU interpreter and PYTHONPATH with CUDA hidden.
Records every opened/listed path, then checks each against out/STAGE_LIST.tsv and flags /home or /data* access."""
import sys, os, json, csv
OPENS, LISTS, WRITES = {}, {}, []
PHASE = ['imports']
def hook(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = os.path.abspath(os.fsdecode(args[0])); mode, flags = args[1], args[2]
        w = (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)) or (isinstance(mode, str) and any(x in mode for x in 'wax+'))
        (WRITES.append((PHASE[0], p)) if w else OPENS.setdefault(p, PHASE[0]))
    elif event in ('os.listdir', 'os.scandir', 'glob.glob') and isinstance(args[0], (str, bytes)):
        LISTS.setdefault(os.path.abspath(os.fsdecode(args[0])), PHASE[0])
sys.addaudithook(hook)
K = '/scratch/jjyeung/orch_n30/sb_ktfix2'
sys.path.insert(0, K+'/code')
from common import *
import runner, uuid
from process_guard import freeze, require_score
PHASE[0] = 'freeze'
root = ROOT/'runtime'/('trace_'+uuid.uuid4().hex[:8])
for part in 'ABCH': freeze(root, part); require_score(root, part)
PHASE[0] = 'population'
from exclusions import population, decision_rows
pop = population(); decision_rows([dict(row_id=i, room=r, split='train') for i, r in list(pop['row_rooms'].items())[:5]])
PHASE[0] = 'gpu_imports'
import gpu_models
sys.path.insert(0, str(ROOT/'code/vendor'))
import geo_bakeoff.backends as B
from depth_anything_3.cfg import create_object, load_config
from depth_anything_3.registry import MODEL_REGISTRY
import evaluate_v2, camera_pricing
PHASE[0] = 'done'
backend_file = B.__file__
sys.audit_hooks_disabled = True
rows = list(csv.DictReader(open(ROOT/'out/STAGE_LIST.tsv'), delimiter='\t'))
files = {r['path'] for r in rows if r['kind'] != 'dir'}; dirs = [r['path'].rstrip('/')+'/' for r in rows if r['kind'] == 'dir']
def covered(p):
    return p in files or any(p.startswith(d) for d in dirs)
def ignorable(p):
    return p.startswith(('/proc/', '/sys/', '/dev/', str(root))) or p.startswith(str(ROOT/'runtime'))
nfs = sorted(p for p in list(OPENS) + list(LISTS) if p.startswith(('/home', '/data')))
unlisted = sorted({p for p in OPENS if not covered(p) and not ignorable(p) and os.path.isfile(p)})
out = dict(backend_file=backend_file, backend_vendored=backend_file.startswith(K+'/code/vendor/'), opens=len(OPENS), lists=len(LISTS),
           nfs_access=nfs, unlisted_opens=unlisted, writes_outside_runtime=sorted({p for _, p in WRITES if not ignorable(p)}),
           phases={ph: sum(v == ph for v in OPENS.values()) for ph in ('imports', 'freeze', 'population', 'gpu_imports')})
open('/scratch/jjyeung/orch_n30/sb_ktchk/work/trace_new.json', 'w').write(json.dumps(out, indent=1))
print(json.dumps(out, indent=1)[:3000])
