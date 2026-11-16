"""Pinned cont_ops conversion of completed Trinity family packets."""
import importlib.util
from pathlib import Path
import sys
import json
import trinity_read as T
import milestone as M

READK = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk')
RECORDS = READK/'kit/reader/records.py'
SCORER = READK/'f1f2.py'
BASELINE = READK/'evidence/A544.jsonl'
RECORDS_SHA = '85ccbed8999dbe3d5770e1824e7eeef510c743c7fef2c5297f68e907a34d73d3'
SCORER_SHA = '15e66c8003f8afc888de5ea204e7262257c14ac18232b1d9490a52084554d116'


def imported(path, pin, name):
    if T.sha(path) != pin: raise ValueError('Pinned source differs: '+str(path))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try: spec.loader.exec_module(module)
    finally: sys.path.pop(0)
    return module


def items(args):
    out = T.writable(args.out); receipt = out.with_suffix('.RECEIPT.json')
    if out.exists() or out.is_symlink() or receipt.exists() or receipt.is_symlink():
        raise ValueError('ITEMS output or receipt exists')
    if type(args.step) is not int or args.step <= 0: raise ValueError('Require positive step')
    reader = Path(args.read).resolve(); summary_path = reader/'MILESTONE_SUMMARY.json'
    summary = T.load(summary_path)
    if summary['status'] != 'complete' or summary['step'] != args.step:
        raise ValueError('Require completed read at requested step')
    families = summary['families']
    if not families or not set(families) <= set(T.FAMILIES): raise ValueError('Invalid families')
    converter = imported(RECORDS, RECORDS_SHA, 'cont_ops_records')
    scorer = imported(SCORER, SCORER_SHA, 'cont_ops_f1f2')
    hashes = {str(summary_path): T.sha(summary_path)}; values = []; counts = {}; journals = {}
    for family, entry in families.items():
        packet = reader/family
        if entry['status'] != 'complete' or Path(entry['packet']).resolve() != packet:
            raise ValueError('Family packet differs')
        paths = [packet/name for name in ('COMPLETE.json', 'EXIT.json', 'CONFIG.json', 'report/B2048.json')]
        complete, exited, config, report = [T.load(p) for p in paths]
        if (complete['family'] != family or exited['returncode'] != 0 or exited.get('yielded') or
                exited.get('sampler_errors') or config['spec']['step'] != args.step):
            raise ValueError('Incomplete or wrong-step family packet')
        M.validate_membership(family, complete['ids'])
        if T.sha(paths[-1]) != entry['report_sha256']:
            raise ValueError('Authenticated B2048 report differs')
        attempt = config['token']
        if not isinstance(attempt, str) or not __import__('re').fullmatch('[a-z][0-9a-f]{8,32}', attempt):
            raise ValueError('Invalid packet attempt')
        journal = packet/'direct'/family/'results/budget_2048/0'/('items_'+attempt+'.jsonl')
        paths.append(journal)
        for path in paths:
            if path.resolve() != path or not path.is_file(): raise ValueError('Nonregular packet input')
            hashes[str(path)] = T.sha(path)
        # Worker journals contain blank separator lines; records() receives records only.
        rows = converter.records(family, report, [s for s in journal.read_text().splitlines() if s.strip()], args.step)
        M.validate_membership(family, [r['id'] for r in rows])
        expected = M.inventory()[family]['items']
        if any(r['task_type'] != expected[r['id']] for r in rows): raise ValueError('Task type differs')
        values.extend(rows); counts[family] = len(rows); journals[family] = str(journal)
    scorer.index(values, args.step)
    baseline_path = Path(args.a) if getattr(args, 'a', None) else BASELINE
    baseline = scorer.load(baseline_path); scorer.index(baseline, 544)
    selected = {f for f in families if f != 'camera'}
    aa = [r for r in baseline if r['family'] in selected]
    bb = [r for r in values if r['family'] in selected]
    if selected: scorer.align(aa, bb)
    hashes[str(baseline_path)] = T.sha(baseline_path)
    for path, pin in hashes.items():
        if T.sha(path) != pin: raise ValueError('Input changed during conversion: '+path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the name exclusively before invoking the unchanged writer.
    with out.open('x'): pass
    converter.write(out, values)
    scorer.index(scorer.load(out), args.step)
    result = dict(schema=1, step=args.step, items_sha256=T.sha(out), counts=counts,
                  inputs_sha256=hashes, records_py_sha256=RECORDS_SHA, f1f2_py_sha256=SCORER_SHA,
                  journals=journals, baseline=str(baseline_path), status='complete')
    T.dump(receipt, result)
    return result
