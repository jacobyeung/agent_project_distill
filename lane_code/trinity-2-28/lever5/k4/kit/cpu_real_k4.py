"""Local rehearsal of the Orchard CPU check: real tower forward on CPU (capture 1, arm A) plus decode of every frame."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parent
GB = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
PAY = GB/'work/payload'
SITE = '/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages'
SERVED = '/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames'
WEIGHTS = Path('/scratch/jjyeung/k1/g3t')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def local_cfg(cfg, frames, work):
    cfg = json.loads(json.dumps(cfg))
    cfg.update(x8=[str(PAY/'tree'), SITE], xl=str(frames), xc=SERVED, xu=str(work/'9.err'))
    for pin in cfg['x9']:
        pin[0] = str(PAY/pin[0].split('/p/', 1)[1])
    cfg['xb'] = dict(cfg['xb'], weights_path=str(WEIGHTS/'model.safetensors'), config_path=str(WEIGHTS/'config.json'))
    return cfg


def extract(work):
    frames = work/'8'
    frames.mkdir()
    for archive in (GB/'orchard_tower2x_b/8.tgz', ROOT/'10.tgz'):
        with tarfile.open(archive) as t:
            for item in t:
                assert item.isfile() and '/' not in item.name and item.name.endswith('.png')
                with (frames/item.name).open('xb') as f:
                    f.write(t.extractfile(item).read())
    return frames


def main():
    work = Path(tempfile.mkdtemp(prefix='real_', dir=ROOT))
    worker = module('worker_real', ROOT/'2.py')
    cfg = json.loads((ROOT/'1.json').read_text())
    frames = extract(work)
    cfg = local_cfg(cfg, frames, work)
    start = time.monotonic()
    result = worker.run(cfg, mode='cpu')
    seconds = time.monotonic()-start
    entry = module('entry_real', ROOT/'0.py')
    raw = worker.write(work/'4.1.json', result)
    arm = result['rows'][0]['arms'][0]
    summary = dict(passed=entry.cpu_passed(json.loads((ROOT/'1.json').read_text()), worker, result),
                   complete=result['complete'], error=result.get('error'), error_detail=result.get('error_detail'),
                   torch_threads=8, seconds=seconds, load_seconds=result.get('load_seconds'),
                   unit_seconds=arm.get('seconds'), unit_inference_seconds=arm.get('inference_seconds'),
                   decode_all_seconds=result.get('decode_all_seconds'),
                   decoded_frames=sum(a['frames'] for r in result.get('decoded', []) for a in r['arms'] if a),
                   decoded_matches=sum(a['raw_match_count'] for r in result.get('decoded', []) for a in r['arms'] if a),
                   rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, return_bytes=len(raw),
                   work=str(work), weights_sha256_pinned=True,
                   scope='Local rehearsal on trinity-2-28 with the pinned weights, local payload mirror and local env; Orchard env versions may differ.')
    if arm.get('status') == 'ok':
        import numpy as np
        c = np.asarray(arm['c2w'])
        summary.update(finite=bool(np.isfinite(c).all()), shape=list(c.shape))
    (ROOT/'CPU_REAL_K4.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
