"""Recheck every synthetic rank-equivalent first batch; this is not planned-run admission."""
import hashlib
import json
import os
import resource
import sqlite3
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
sys.path[:0] = [str(SRC / 'work/scripts'), str(SRC / 'pkg/work/tree_f64')]
os.environ.update(STUDENT_ORCHARD='1', STUDENT_FRAME_ROOT_MAP='{}')
reads = {str(Path(__file__))}
def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        if (args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            if not p.is_relative_to(ROOT): raise RuntimeError('Write outside review: ' + str(p))
        elif p.is_relative_to(SRC): reads.add(str(p))
sys.addaudithook(guard)
import torch
torch.set_num_threads(8)
import f64_dryrun as D
from student_pilot.carrier_c1_run import Rows, processor_for_receipt, check_row
cfgpath = SRC / 'out/kit/configs/r1_config_f64.json'
cfg = json.loads(cfgpath.read_text())
stores = {}
for stream in ('pose', 'vqa', 'routing', 'pointing'):
    db = SRC / 'work/dryrun/f64/a43' / stream / 'rows.sqlite'
    reads.add(str(db))
    with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as connection:
        count = connection.execute('SELECT count(*) FROM rows').fetchone()[0]
    stores[stream] = dict(database=dict(path=str(db), sha256=hashlib.sha256(db.read_bytes()).hexdigest()), count=count)
# Use the exact camera/depth input named by the submitted script, never infer a receipt.
if not D.PREP.is_file():
    raise FileNotFoundError('MISSING: ' + str(D.PREP))
reads.add(str(D.PREP))
receipt = D.receipt_for(cfg, stores)
processor = processor_for_receipt({'root': str(D.META)}, receipt)
rows = Rows(receipt, processor)
first = D.plan_rows(receipt, cfg['world_size'])
print('Loading full 32-layer random-init architecture; fixture sampler only.', flush=True)
start = time.perf_counter()
model = D.build_model(receipt, processor)
model.eval()
print('Model loaded in %.1f seconds' % (time.perf_counter() - start), flush=True)
records = []
for rank, index in enumerate(first['pose'][1]):
    batch, targets, audit = rows.get('pose', index)
    check_row(batch, targets, 'pose', model)
    start = time.perf_counter()
    with torch.no_grad(): result = model(batch, targets, stream='pose')
    loss = float(result['loss'])
    components = {k: float(v) for k, v in result['components'].items()}
    record = dict(rank=rank, index=int(index), tokens=int(batch['input_ids'].shape[-1]), loss=loss,
                  finite=all(__import__('math').isfinite(v) for v in [loss, *components.values()]),
                  seconds=round(time.perf_counter() - start, 2), components=components,
                  peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20)
    records.append(record)
    print(json.dumps(record), flush=True)
rows.close()
provenance = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads) if Path(p).is_file()}
value = dict(command='bash run_cpu.sh forward_check.py', input_sha256=provenance,
    scope='Synthetic a43 stores and substitute mixed_indices sampler; actual bound first batches are MISSING.',
    torch=torch.__version__, threads=torch.get_num_threads(), layers=model.config.text_config.num_hidden_layers,
    total_parameters=sum(p.numel() for p in model.parameters()),
    heads_total=sum(p.numel() for p in model.auxiliary_heads.parameters()),
    heads_trainable=sum(p.numel() for p in model.auxiliary_heads.parameters() if p.requires_grad),
    records=records)
(ROOT / 'out/forward_review.json').write_text(json.dumps(value, indent=2) + '\n')
