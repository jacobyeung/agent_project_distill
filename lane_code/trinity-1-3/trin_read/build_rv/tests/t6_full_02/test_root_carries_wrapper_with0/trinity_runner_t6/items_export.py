"""Export full authenticated family packets through the pinned cont_ops scorer."""
import importlib.util
import json
from pathlib import Path
import sys
import trinity_read as T
import milestone as M

READK = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk')
RECORDS = READK/'kit/reader/records.py'
RECORDS_SHA = '85ccbed8999dbe3d5770e1824e7eeef510c743c7fef2c5297f68e907a34d73d3'
F1F2 = READK/'f1f2.py'
F1F2_SHA = '15e66c8003f8afc888de5ea204e7262257c14ac18232b1d9490a52084554d116'
A544 = READK/'evidence/A544.jsonl'
CORE = ('main', 'away', 'forward')


def pinned_import(path, digest, name):
    if T.sha(path) != digest: raise ValueError('Scorer source SHA256 differs: '+str(path))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    # f1f2 imports its local room_bootstrap dependency; never copy its code.
    sys.path.insert(0, str(path.parent))
    try: spec.loader.exec_module(module)
    finally: sys.path.pop(0)
    return module


def export_items(args):
    if type(args.step) is not int or args.step <= 0: raise ValueError('Require positive step')
    root = Path(args.read).resolve(); out = T.writable(args.out)
    receipt_path = out.with_suffix('.RECEIPT.json')
    if out.exists() or receipt_path.exists(): raise ValueError('ITEMS output or receipt exists')
    summary_path = root/'MILESTONE_SUMMARY.json'; summary = T.load(summary_path)
    families = summary['families']
    if (summary['status'] != 'complete' or summary['step'] != args.step or
            not set(CORE) <= set(families) or not set(families) <= set(T.FAMILIES)):
        raise ValueError('Require completed full main/away/forward milestone at requested step')
    records = pinned_import(RECORDS, RECORDS_SHA, 'trin_records')
    scorer = pinned_import(F1F2, F1F2_SHA, 'trin_f1f2')
    inputs = {}
    def pin(path):
        if not path.is_file() or path.resolve() != path: raise ValueError('Input must be regular without symlinks')
        inputs[str(path)] = dict(bytes=path.stat().st_size, sha256=T.sha(path))
    pin(summary_path)
    values = []; counts = {}; journals = {}
    for family in T.FAMILIES:
        if family not in families: continue
        row = families[family]; packet = root/family
        complete_path = packet/'COMPLETE.json'; exit_path = packet/'EXIT.json'
        complete = T.load(complete_path); execution = T.load(exit_path)
        if (row['status'] != 'complete' or complete['family'] != family or
                execution['returncode'] != 0 or execution.get('yielded') or execution.get('sampler_errors')):
            raise ValueError('Incomplete family packet')
        M.validate_membership(family, complete['ids'])
        report_path = packet/'report/B2048.json'
        journal_path = packet/'direct'/family/'results/budget_2048/0/items_a0.jsonl'
        for path in (complete_path, exit_path, report_path, journal_path): pin(path)
        if inputs[str(report_path)]['sha256'] != row['report_sha256']:
            raise ValueError('Authenticated report SHA256 differs')
        # New packets authenticate both files at completion; summary authenticates the report too.
        for path in (report_path, journal_path):
            relative = str(path.relative_to(packet))
            if complete.get('input_sha256', {}).get(relative) != inputs[str(path)]['sha256']:
                raise ValueError('Packet input SHA256 differs: '+relative)
        with journal_path.open() as stream:
            result = records.records(family, T.load(report_path), stream, args.step)
        M.validate_membership(family, [r['id'] for r in result])
        expected = M.inventory()[family]['items']
        if any(expected[r['id']] != r['task_type'] for r in result): raise ValueError('Task inventory differs')
        counts[family] = len(result); values.extend(result)
        journals[family] = str(journal_path)
    scorer.index(values, args.step)
    core = [r for r in values if r['family'] in CORE]
    pin(A544)
    scorer.align(scorer.load(A544), core)
    if getattr(args, 'a', None):
        a = Path(args.a).resolve(); pin(a)
        scorer.align(scorer.load(a), core)
    # Validate and hash every input again before publishing either output.
    for path, pin_value in inputs.items():
        if T.sha(path) != pin_value['sha256']: raise ValueError('Input changed during export')
    out.parent.mkdir(parents=True, exist_ok=True)
    with T.lock(out.with_name(out.name+'.lock')):
        if out.exists() or receipt_path.exists(): raise ValueError('ITEMS output or receipt exists')
        # write() is the unchanged scorer implementation; reserve its filename exclusively first.
        with out.open('x'): pass
        records.write(out, values)
        scorer.index(scorer.load(out), args.step)
        receipt = dict(schema=1, step=args.step, items=str(out), sha256=T.sha(out), counts=counts,
                       inputs=inputs, journals=journals,
                       records=dict(path=str(RECORDS), sha256=RECORDS_SHA),
                       f1f2=dict(path=str(F1F2), sha256=F1F2_SHA),
                       journal_layout='direct/<family>/results/budget_2048/0/items_a0.jsonl; Trinity direct packet uses the Orchard a0 attempt without the outer a0 directory')
        T.dump(receipt_path, receipt)
    return receipt
