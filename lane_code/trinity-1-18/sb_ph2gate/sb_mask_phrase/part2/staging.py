"""Inventory the GPU payload from the frozen plan and actual local files; never copy data."""
import collections
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import sam3_pass as G

DEST = G.HERE.parent/'out'


def main():
    plans = {'default': G.plan(), 'all_aliases': G.plan(True)}
    files, expected = {}, {}
    def add(path, role, pin=None):
        path = Path(path)
        files.setdefault(path, set()).add(role)
        if pin:
            if path in expected and expected[path] != pin:
                raise ValueError(f'conflicting pins: {path}')
            expected[path] = pin
    add(G.CHECKPOINT, 'checkpoint', G.CHECKPOINT_SHA)
    add(G.RECEIPT, 'source_receipt')
    receipt = json.loads(G.RECEIPT.read_text())
    for rel, pin in receipt['source_files'].items():
        add(G.SOURCE_ROOT/rel, 'sam_source', pin)
    # Whole source packages include runtime imports and tokenizer assets.
    for folder, role in ((G.SOURCE_ROOT/'sam3', 'sam_source'),
                         (G.TREE/'student_pilot', 'reader_source')):
        for p in sorted(folder.rglob('*')):
            if '__pycache__' not in p.parts and p.is_file() and p.suffix != '.pyc':
                add(p, role)
    for p in (G.BOX/'reader_src/e2e_reader/__init__.py', G.BOX/'reader_src/e2e_reader/stage1.py',
              G.VENDOR/'vendor/sam3_tower.py'):
        add(p, 'reader_source')
    for p in (G.IDS, G.BOX/'pinned_train.json', G.DECISION, G.NEW, G.NEW_SHA,
              G.HERE/'part2/BARS_PART2.json', G.HERE/'part2/BARS_PART2.sha256', G.VENDOR/'variantlib.py'):
        add(p, 'plan_input')
    for name in ('sam3_pass.py', 'gate.py', 'staging.py'):
        add(G.HERE/'part2'/name, 'entrypoint')
    for c, _ in plans['default']:
        for slot in c['anchor_slots']:
            rec = c['dense_frames'][slot]
            add(rec['path'], 'anchor_frame', rec['sha256'])
        if c['canonical'] == G.STEP5_CAPTURE:
            add(G.K1/G.digest(c['canonical'])[:16]/'candidates.json', 'step5_raw_cache')
    rows, pins = [], {}
    for p in sorted(files):
        if not p.is_file() or not str(p.resolve()).startswith('/scratch/'):
            rows.append(dict(path=str(p), roles=sorted(files[p]), status='MISSING', bytes=None))
            continue
        actual = G.sha(p)
        pins[str(p)] = actual
        rows.append(dict(path=str(p), roles=sorted(files[p]), bytes=p.stat().st_size, sha256=actual,
                         expected_sha256=expected.get(p), status='PASS' if p not in expected or actual == expected[p] else 'FAIL'))
    totals = {}
    for role in sorted({r for rs in files.values() for r in rs}):
        subset = [r for r in rows if role in r['roles']]
        totals[role] = dict(files=len(subset), bytes=sum(r['bytes'] or 0 for r in subset))
    estimates = {}
    for name, plan in plans.items():
        calls = sum(G.distinct(k) for _, k in plan)
        estimates[name] = dict(captures=len(plan), calls=calls, prompt_frames=calls*32,
                               gpu_h=calls*32*.064/3600, hard_cap_gpu_h=G.HARD_GPU_H)
    spec = G.HERE/'in/v3/KIT_SPEC_mask_phrase_v2.md'
    pins[str(spec)] = G.sha(spec)
    result = dict(status='PASS' if all(r['status'] == 'PASS' for r in rows) else 'MISSING_OR_FAIL',
                  scope='GPU step5 and pool pass payload; existing SAM3 Python environment is a prerequisite, not included; CPU pricing dependencies are separate',
                  environment='/scratch/jjyeung/envs/sam3_capretry_native_v1',
                  command='bash sb_mask_phrase/run.sh part2/staging.py',
                  files=len(rows), bytes=sum(r['bytes'] or 0 for r in rows), groups=totals,
                  estimates=estimates, estimate_basis='0.064 GPU-seconds per prompt-frame, from the v3 spec; excludes loading, step5 and encoding overhead',
                  inventory=rows, input_sha256=pins)
    DEST.mkdir(exist_ok=True)
    (DEST/'STAGING_PART2.json').write_text(json.dumps(result, indent=1)+'\n')
    (DEST/'STAGING_PART2.tsv').write_text('bytes\tsha256\troles\tstatus\tpath\n'+''.join(
        f"{r['bytes']}\t{r.get('sha256', 'MISSING')}\t{','.join(r['roles'])}\t{r['status']}\t{r['path']}\n" for r in rows))
    print(json.dumps({k: v for k, v in result.items() if k not in ('inventory', 'input_sha256')}, indent=1))


if __name__ == '__main__':
    main()
