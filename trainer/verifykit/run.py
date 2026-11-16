"""Streaming batched verification with resumable, input-bound JSONL output."""
import argparse
import json
import math
import time
from pathlib import Path
import numpy as np
from PIL import Image
from .io import rows, validate, mask_for, frame_path, dump, sha, digest
from .render import render, sheet, prompt
from .model import HFBackend, StubBackend


def plan(groups, form, variant='outline'):
    requests = []
    for g in groups:
        cs = g['candidates']
        chunks = [[c] for c in cs] if form == 'V1' else [cs[i:i+5] for i in range(0, len(cs), 5)]
        if form == 'V3':
            if 'v3_slots' not in g: raise ValueError('V3 requires explicit MDG or labelled oracle presence ranking')
            chunks = [[dict(slot=k)] for k in g['v3_slots']]
        for i, chunk in enumerate(chunks):
            ids = [c['candidate_id'] for c in chunk] if form != 'V3' else []
            req = dict(request_id=g['object_id']+'::'+form+f'::{i}', object_id=g['object_id'],
                scene=g['scene'], name=g['name'], form=form, variant=variant, candidate_ids=ids,
                slots=[c['slot'] for c in chunk], prompt=prompt(form, g['name'], variant),
                oracle=bool(g.get('oracle')) or (form == 'V3' and g.get('v3_presence_source') == 'GT_PRESENCE_ORACLE'),
                presence_source=g.get('v3_presence_source') if form == 'V3' else g.get('presence_source'))
            requests.append((req, g, chunk))
    return requests


def materialize(item):
    req, group, candidates = item
    if req['form'] == 'V3':
        with Image.open(frame_path(group, candidates[0]['slot'])) as image:
            return image.convert('RGB'), []
    images, metadata = [], []
    for c in candidates:
        with Image.open(frame_path(group, c['slot'])) as image:
            image, meta = render(image, mask_for(c), req['variant'])
        images.append(image); metadata.append(meta)
    return (images[0] if req['form'] == 'V1' else sheet(images)), metadata


def run(a, backend=None):
    groups = validate(rows(a.candidates))
    requests = plan(groups, a.form, a.variant)
    code = {p.name:sha(p) for p in Path(__file__).parent.glob('*.py')}
    config = dict(candidates_sha256=sha(a.candidates), checkpoint=str(Path(a.checkpoint).resolve()) if a.checkpoint else 'STUB',
                  form=a.form, variant=a.variant, stub=a.stub, code=code)
    metadata_path = Path(str(a.candidates)+'.meta.json')
    if metadata_path.exists():
        config['candidate_metadata_sha256'] = sha(metadata_path)
    if not a.stub:
        cp = Path(a.checkpoint)
        config['checkpoint_files'] = {str(p.relative_to(cp)):dict(size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)
            for p in sorted(cp.glob('*')) if p.is_file()}
    binding = digest(config)
    checkpoint_id = digest({k:config.get(k) for k in ('checkpoint', 'checkpoint_files')})
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out.exists():
        with out.open() as f:
            for line in f:
                if not line.strip(): continue
                try: row = json.loads(line)
                except json.JSONDecodeError: continue
                if row['binding'] != binding: raise ValueError('Resume binding differs; choose a new output file')
                done[row['request_id']] = row
    pending = [r for r in requests if r[0]['request_id'] not in done]
    count = len(pending)
    if a.limit: pending = pending[:a.limit]
    if a.dry_run:
        report = dict(total_calls=len(requests), pending=count, planned=len(pending), batches=math.ceil(len(pending)/a.batch_size), config=config)
        dump(str(out)+'.plan.json', report); print(json.dumps(report)); return report
    backend = backend or (StubBackend() if a.stub else HFBackend(a.checkpoint, a.device))
    started = time.monotonic(); completed = 0; pilot_written = False
    with out.open('a') as stream:
        for start in range(0, len(pending), a.batch_size):
            batch = pending[start:start+a.batch_size]
            images_meta = [materialize(item) for item in batch]
            results = backend.predict([x[0] for x in batch], [x[0] for x in images_meta])
            for item, result, (_, metadata) in zip(batch, results, images_meta):
                row = dict(item[0], **result, render=metadata, binding=binding, checkpoint_id=checkpoint_id)
                if a.form == 'V1': row['p_yes'] = row['probabilities'][0]
                if a.form == 'V2':
                    p = row['probabilities']; allowed = [p[0]]+p[1:len(row['candidate_ids'])+1]
                    row['choice'] = int(np.argmax(allowed))
                stream.write('\n'+json.dumps(row, allow_nan=False)+'\n')
            stream.flush(); completed += len(batch)
            elapsed = time.monotonic()-started
            if completed >= 256 and not pilot_written:
                pilot = dict(calls=completed, seconds=elapsed, calls_per_second=completed/elapsed,
                    projected_total_gpu_hours=elapsed/completed*len(requests)/3600,
                    projected_remaining_gpu_hours=elapsed/completed*(count-completed)/3600,
                    stub=a.stub, excludes_model_load=True)
                dump(str(out)+'.pilot256.json', pilot); print(json.dumps(pilot), flush=True); pilot_written=True
            if a.max_seconds and elapsed >= a.max_seconds: break
    report = dict(total_calls=len(requests), completed_this_run=completed, completed_before=len(done),
        remaining=len(requests)-len(done)-completed, seconds=time.monotonic()-started, config=config,
        processor_parity=getattr(backend, 'parity', []), stub=a.stub)
    dump(str(out)+'.run.json', report)
    print(json.dumps({k:v for k,v in report.items() if k!='config'}))
    return report


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--checkpoint'); p.add_argument('--form', choices=['V1','V2','V3'], required=True)
    p.add_argument('--candidates', required=True); p.add_argument('--out', required=True)
    p.add_argument('--batch-size', type=int, default=4); p.add_argument('--variant', choices=['outline','plain','dim'], default='outline')
    p.add_argument('--stub', action='store_true'); p.add_argument('--device', default='cuda')
    p.add_argument('--limit', type=int); p.add_argument('--dry-run', action='store_true'); p.add_argument('--max-seconds', type=float)
    a = p.parse_args()
    if a.batch_size < 1 or (a.limit is not None and a.limit < 1): p.error('Batch size and limit must be positive')
    if not a.stub and not a.checkpoint: p.error('--checkpoint is required unless --stub')
    run(a)

if __name__ == '__main__': main()
