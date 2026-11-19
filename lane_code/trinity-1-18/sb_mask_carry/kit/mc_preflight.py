"""CPU preflight for the GPU pass (SAM 3 interpreter, CUDA hidden): staged inputs present with their recorded sizes,
sam3 resolves to the pinned /scratch source, seeds current with PHRASE_SET.json, and room for outputs. Exit 1 on any failure."""
import json, os, shutil, sys
from pathlib import Path
import mc_common as C


def main():
    fails = []
    staging = json.loads((C.OUT/'STAGING.json').read_text())
    for item in staging['items']:
        paths = item['path'] if isinstance(item['path'], list) else [item['path']]
        missing = [p for p in paths if not Path(p).exists()]
        if missing:
            fails.append(f"{item['kind']}: missing {missing[:3]}")
    frames = (C.OUT/'STAGING_FRAMES.txt').read_text().split()
    absent = [p for p in frames if not os.path.exists(p)]
    if absent:
        fails.append(f'{len(absent)} of {len(frames)} frames missing, e.g. {absent[:2]}')
    if C.CHECKPOINT.stat().st_size != 3450062241:
        fails.append('checkpoint size differs from 3,450,062,241 bytes')
    seeds = json.loads((C.OUT/'seeds/SEEDS.json').read_text())
    phr = seeds['summary']['S_PHR']['status']
    if C.PHRASE_SET.exists():
        have = C.sha256_file(C.PHRASE_SET)
        if phr != 'PRESENT' or have != seeds['summary']['S_PHR'].get('phrase_set_sha256'):
            fails.append(f'PHRASE_SET.json ({have[:16]}) is not the one SEEDS.json was built from (S_PHR {phr}): '
                         'rerun mc_seeds.py all and the dry run first')
    sys.path.insert(0, str(C.SAM3_ROOT))
    import sam3
    if not str(Path(sam3.__file__).resolve()).startswith(str(C.SAM3_ROOT)+'/'):
        fails.append('sam3 resolves outside the pinned source: '+sam3.__file__)
    import torch
    if torch.__version__ != '2.10.0+cu128':
        fails.append('torch '+torch.__version__)
    free = shutil.disk_usage(C.OUT).free
    if free < 150*2**30:
        fails.append(f'/scratch free {free/2**30:.0f} GiB < 150 GiB (outputs plus the 100-200 GB the node keeps free)')
    print(json.dumps(dict(passed=not fails, fails=fails, frames=len(frames), S_PHR=phr)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
