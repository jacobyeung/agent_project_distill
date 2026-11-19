#!/usr/bin/env python3
"""Count pricing kit (lane sb_countdesign, 2026-11-19): run the frozen SAM 3 tower at lane b05_owngrd's teacher contract
(joint floor 0.2, cap 10, resolution 1008, bf16) over a manifest written by build_count_manifest.py.

It reuses owngrd.teacher.TowerBackend and run_capture unchanged and skips owngrd's eligibility gate, which admits training captures
only: this runner serves the dev pricing read and nothing else. Its outputs are evaluation evidence and never training labels.

Run from the owngrd code root (/scratch/jjyeung/orch_n30/b05_owngrd/code):
  <env python> <kit>/run_count_teacher.py --manifest M.json --manifest-sha256 <sha> --out OUT --settings settings_gpu.json [--shard i/n] [--hours 2]
  add --stub for the CPU dry run (owngrd's stub tower; frames are still read and hash-checked)."""
import argparse, gzip, json, os, sys, time
from pathlib import Path
sys.path.insert(0, os.getcwd())
from owngrd import teacher as T
from owngrd.common import atomic_write_bytes, atomic_write_json, sha256_file, sha256_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True); ap.add_argument('--manifest-sha256', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--settings'); ap.add_argument('--stub', action='store_true'); ap.add_argument('--shard', default='0/1'); ap.add_argument('--hours', type=float, default=2.0)
    a = ap.parse_args()
    if sha256_file(a.manifest) != a.manifest_sha256: raise SystemExit('manifest sha256 differs')
    man = json.loads(Path(a.manifest).read_text())
    if man.get('schema') != 'owngrd-teacher-manifest-v1' or man.get('source', {}).get('set') not in ('R0-dev', 'dev-S1'):
        raise SystemExit('this runner serves the dev count pricing manifests only')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'DEV_PRICING_READ_NEVER_TRAINING_LABELS.txt').write_text('Outputs of the count pricing read on %s. Evaluation evidence only.\n' % man['source']['set'])
    i, n = (int(x) for x in a.shard.split('/'))
    if a.stub:
        from owngrd.stub_tower import StubTower
        backend = StubTower(T.CONTRACT['joint_floor'], T.CONTRACT['cap'])
    else:
        backend = T.TowerBackend(json.loads(Path(a.settings).read_text()), T.CONTRACT['joint_floor'], T.CONTRACT['cap'])
    journal = open(out / ('PROGRESS.%dof%d.jsonl' % (i, n)), 'a'); deadline = time.time() + a.hours * 3600
    for c in [c for k, c in enumerate(man['captures']) if k % n == i]:
        d = out / T.capture_key(c['canonical'])
        if (d / 'DONE.json').exists(): continue
        if time.time() > deadline:
            journal.write(json.dumps({'event': 'time_cap', 'unix': time.time()}) + '\n'); journal.flush(); return 3
        d.mkdir(exist_ok=True)
        result, secs = T.run_capture(backend, c, verify=True)
        atomic_write_bytes(d / 'teacher.json.gz', gzip.compress(json.dumps(result, allow_nan=False).encode(), 6))
        done = {'canonical': c['canonical'], 'teacher_sha256': sha256_file(d / 'teacher.json.gz'), 'seconds': secs, 'frames': len(c['frames']),
                'names': len(c['names']), 'manifest_sha256': a.manifest_sha256, 'contract_sha256': sha256_json(T.CONTRACT), 'host': os.uname().nodename, 'unix': time.time()}
        atomic_write_json(d / 'DONE.json', done)
        journal.write(json.dumps({'event': 'capture_done', **done}) + '\n'); journal.flush()
    journal.write(json.dumps({'event': 'shard_complete', 'unix': time.time()}) + '\n'); journal.flush()
    return 0

if __name__ == '__main__':
    sys.exit(main())
