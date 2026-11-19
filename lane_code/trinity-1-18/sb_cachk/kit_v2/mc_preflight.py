"""CPU preflight for the GPU pass (SAM 3 interpreter, CUDA hidden). Exit 1 unless every check holds:
every STAGING.json item, the control files included, is present with its recorded bytes and every staged frame exists;
the seeds' S_PHR provenance names the fold file mc_common resolves now, and that file, its DECISION.json and its BARS.json
hash to the recorded sha256 (no fold file: the seeds hold S_PHR NOT_YET); the population digest and its ruling bytes
hold; the frozen bars and their amendment agree; the pinned vnice and terminator hash to their pins; sam3 resolves to
the pinned /scratch source under torch 2.10.0+cu128; /scratch keeps 150 GiB free.
Usage: python mc_preflight.py
"""
import json, os, shutil, sys
from pathlib import Path
import mc_common as C


def phrase_check(summary, folds_path):
    """Reasons the seeds' S_PHR provenance disagrees with the fold file at folds_path ([] when they agree)."""
    s, folds_path = summary['S_PHR'], Path(folds_path)
    if not folds_path.exists():
        return [] if s['status'] != 'PRESENT' else [f"SEEDS.json carries S_PHR from {s['phrase_folds']['path']} but {folds_path} is absent: rerun mc_seeds.py all"]
    if s['status'] != 'PRESENT':
        return [f"{folds_path} exists but SEEDS.json has S_PHR {s['status']}: rerun mc_seeds.py all (CPU) first"]
    prov, fails = s.get('phrase_folds') or {}, []
    if prov.get('path') != str(folds_path):
        fails.append(f"SEEDS.json S_PHR came from {prov.get('path')}, mc_common resolves {folds_path}: rerun mc_seeds.py all")
    for key, sha in (('path', 'sha256'), ('decision', 'decision_sha256'), ('bars_file', 'bars_sha256')):
        p = prov.get(key)
        if not p or not Path(p).exists():
            fails.append(f'S_PHR provenance {key} {p} is missing')
        elif C.sha256_file(p) != prov.get(sha):
            fails.append(f'{p} sha256 differs from the seeds\' provenance ({key}): rerun mc_seeds.py all')
    return fails


def staging_check(staging):
    fails = []
    for item in staging['items']:
        paths = item['path'] if isinstance(item['path'], list) else [item['path']]
        missing = [p for p in paths if not Path(p).exists()]
        if missing:
            fails.append(f"{item['kind']}: missing {missing[:3]}")
        elif item.get('check_bytes') and Path(paths[0]).stat().st_size != item['bytes']:
            fails.append(f"{item['kind']}: {Path(paths[0]).stat().st_size} bytes, staged {item['bytes']}")
    return fails


def main():
    fails = []
    staging = json.loads((C.OUT/'STAGING.json').read_text())
    fails += staging_check(staging)
    frames = (C.OUT/'STAGING_FRAMES.txt').read_text().split()
    absent = [p for p in frames if not os.path.exists(p)]
    if absent:
        fails.append(f'{len(absent)} of {len(frames)} frames missing, e.g. {absent[:2]}')
    if C.CHECKPOINT.stat().st_size != C.CHECKPOINT_BYTES:
        fails.append(f'checkpoint size differs from {C.CHECKPOINT_BYTES:,} bytes')
    for name, sha in C.VENDOR_SHA256.items():
        if C.sha256_file(C.KIT/'vendor'/name) != sha:
            fails.append(f'kit_v2/vendor/{name} differs from its pin')
    try:
        pop = C.population()
        if C.sha256_file(pop['ruling']['path']) != pop['ruling']['sha256']:
            fails.append('RULING_1056Z.md differs from the bytes POPULATION.json records')
    except (OSError, ValueError, KeyError) as e:
        fails.append(f'POPULATION.json: {e}')
        pop = None
    if not (C.OUT/'BARS_FROZEN.json').exists() or not C.BARS_AMENDMENT.exists():
        fails.append('BARS_FROZEN.json or BARS_AMENDMENT.json missing: bars are registered before any priced number')
    else:
        amend = json.loads(C.BARS_AMENDMENT.read_text())
        if amend['bars_frozen_sha256'] != C.sha256_file(C.OUT/'BARS_FROZEN.json'):
            fails.append('BARS_AMENDMENT.json amends another BARS_FROZEN.json')
        if pop and amend['population']['population_id'] != pop['population_id']:
            fails.append('BARS_AMENDMENT.json registers another population')
    seeds = json.loads((C.OUT/'seeds/SEEDS.json').read_text())
    fails += phrase_check(seeds['summary'], C.PHRASE_FOLDS)
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
    print(json.dumps(dict(passed=not fails, fails=fails, frames=len(frames), S_PHR=seeds['summary']['S_PHR']['status'],
                          phrase_folds=str(C.PHRASE_FOLDS), population_id=pop and pop['population_id'])))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
