"""Annotate sealed budget arms on CPU while retaining their original evidence."""
import json
from pathlib import Path
from budget import BUDGETS, classify
from budget_admission import BudgetContext
from data import tasks_for
from evalpath.items import digest
from journal import annotation_records, records, retain
from provenance import (VERSION, evidence_path, preserve_input, request, sha,
                        verify_annotation, check_config)
from token_audit import token_ids


def _unique(rows):
    unique, raw = {}, {}
    for row, text in rows:
        if row.get('status') != 'complete':
            raise ValueError('Budget annotation requires complete rows')
        retain(unique, row)
        raw.setdefault(row['key'], text)
    return {key: (row, raw[key]) for key, row in unique.items()}


def _convert(cfg, cell, budget, tokenizer, old_sources, sources, rows, receipts,
             original_sha, receipts_sha):
    if budget not in BUDGETS:
        raise ValueError('Unknown budget arm')
    context = BudgetContext(cfg, cell, budget, tokenizer)
    tasks = {t['benchmark']+':'+t['example_id']: t for spec in cfg['datasets']
             if spec['benchmark'] in cfg['cells'][cell]['benchmarks']
             for t in tasks_for(spec, cfg['roots'])}
    arms, metas = _unique(rows), _unique(receipts)
    old_sources = _unique([(r, raw) for r, raw in old_sources if r.get('status') == 'complete'])
    sources = _unique([(r, raw) for r, raw in sources if r.get('status') == 'complete'])
    # All receipts, including orphans, must refer to the authenticated ON journal.
    candidates = {}
    for receipt, _ in metas.values():
        key = receipt.get('source_key')
        if key not in old_sources or receipt.get('binding') != context.arm_binding:
            raise ValueError('Legacy budget receipt binding/source differs')
        if receipt.get('source_sha256') != digest(old_sources[key][0]):
            raise ValueError('Legacy budget source hash differs')
        if receipt.get('budget') != budget or receipt.get('arm') != f'B{budget}':
            raise ValueError('Legacy budget receipt arm differs')
        if receipt.get('key') not in (key, key+':'+str(receipt.get('record_sha256'))):
            raise ValueError('Legacy budget receipt key differs')
        if 'layout' in receipt and receipt['layout'] != cfg['cells'][cell]['layout']:
            raise ValueError('Legacy budget receipt layout differs from bound cell')
        candidates.setdefault(key, []).append(receipt)
    converted, converted_receipts = [], []
    for key, (old, raw) in arms.items():
        matches = [r for r in candidates.get(key, []) if r.get('record_sha256') == digest(raw)]
        if len(matches) != 1 or key not in sources or key not in tasks:
            raise ValueError('Legacy budget receipt/membership differs')
        receipt = matches[0]
        source = sources[key][0]
        classification = classify(tokenizer, token_ids(source, tokenizer), budget)
        if any(receipt.get(k) != v for k, v in classification.items()):
            raise ValueError('Legacy budget classification differs')
        reuse = not classification['forced_close'] and not classification['stopped_unclosed'] and not receipt.get('derivation_error')
        policy = 'reuse_full_on_answer' if reuse else 'continuation_64'
        if receipt.get('answer_cap_policy', policy) != policy:
            raise ValueError('Legacy budget cap policy differs')
        if 'layout' in old and old['layout'] != cfg['cells'][cell]['layout']:
            raise ValueError('Legacy budget layout differs from bound cell')
        if any(k in old for k in ('annotation_version', 'layout_source', 'original_journal_sha256')):
            raise ValueError('Budget journal is already annotated')
        if reuse:
            if old != old_sources[key][0]:
                raise ValueError('Legacy reused ON row differs')
            new, new_raw = sources[key]
        else:
            new = dict(old, layout=cfg['cells'][cell]['layout'], layout_source='bound_config',
                       original_journal_sha256=original_sha, annotation_version=VERSION)
            new_raw = json.dumps(new, allow_nan=False)
        new_receipt = dict(receipt, key=key+':'+digest(new_raw), source_sha256=digest(source),
                           record_sha256=digest(new_raw), answer_cap_policy=policy,
                           layout=cfg['cells'][cell]['layout'], layout_source='bound_config',
                           original_receipts_sha256=receipts_sha, annotation_version=VERSION)
        context.add(source, new, new_raw, new_receipt, tasks[key])
        converted.append((new, new_raw))
        converted_receipts.append(new_receipt)
    return converted, converted_receipts


def _inputs(source_path, cfg, cell):
    annotation = verify_annotation(source_path, cfg, cell)
    if annotation.metadata['version'] != VERSION:
        raise ValueError('Budget annotation requires a portable ON annotation')
    old_path = evidence_path(source_path, annotation.metadata['original_journal'])
    return annotation_records(old_path)[0], list(records(source_path))


def annotate_budget(request_path, archive, original, target, cell, budget, source_path, tokenizer):
    cfg = request(request_path, archive)
    source_path, original, target = map(lambda p: Path(p).resolve(), (source_path, original, target))
    if source_path.parent != target.parent:
        raise ValueError('Keep annotated ON and budget journals in the same cell directory')
    receipt_path = original.with_suffix('.meta.jsonl')
    outputs = (target, target.with_suffix('.meta.jsonl'), target.with_suffix('.annotation.json'))
    if any(p.exists() for p in outputs):
        raise ValueError('Annotation requires new output paths')
    original_sha, receipts_sha, source_sha = sha(original), sha(receipt_path), sha(source_path)
    old_sources, sources = _inputs(source_path, cfg, cell)
    rows, recovery = annotation_records(original)
    receipts, receipt_recovery = annotation_records(receipt_path)
    # Resolve only the original pinned bundle location for task loading.
    resolved = json.loads(json.dumps(cfg).replace('$Q', str(Path(request_path).resolve().parent)))
    converted, new_receipts = _convert(resolved, cell, budget, tokenizer, old_sources, sources,
                                      rows, receipts, original_sha, receipts_sha)
    meta = dict(version=VERSION, kind='budget', layout_source='bound_config', budget=budget,
                cell_index=cell, cell_binding=digest(dict(request=cfg['binding'], cell=cell, budget=budget)),
                original_journal=preserve_input(original, target, 'budget.jsonl'),
                original_journal_sha256=original_sha,
                original_receipts=preserve_input(receipt_path, target, 'receipts.jsonl'),
                original_receipts_sha256=receipts_sha,
                request_path=preserve_input(request_path, target, 'request.json'), request_sha256=sha(request_path),
                source_archive=preserve_input(archive, target, 'source.tar'), source_sha256=cfg['source_sha256'],
                on_journal=source_path.name, on_journal_sha256=source_sha,
                rows=len(converted), receipt_recovery=receipt_recovery, **recovery)
    if (sha(original), sha(receipt_path), sha(source_path)) != (original_sha, receipts_sha, source_sha):
        raise ValueError('Original budget inputs changed during annotation')
    with outputs[0].open('x') as stream:
        for _, raw in converted:
            stream.write(raw+'\n')
    with outputs[1].open('x') as stream:
        for receipt in new_receipts:
            stream.write(json.dumps(receipt, allow_nan=False)+'\n')
    meta.update(annotated_sha256=sha(target), annotated_receipts_sha256=sha(outputs[1]))
    with outputs[2].open('x') as stream:
        stream.write(json.dumps(meta, indent=2)+'\n')
    return meta


def verify_budget_annotation(path, cfg, cell, budget, source_path, tokenizer):
    path = Path(path)
    meta = json.loads(path.with_suffix('.annotation.json').read_text())
    if (meta.get('version'), meta.get('kind'), meta.get('cell_index'), meta.get('budget')) != (VERSION, 'budget', cell, budget):
        raise ValueError('Budget annotation protocol/cell/arm differs')
    def evidence(name):
        return evidence_path(path, meta[name])
    original_cfg = request(evidence('request_path'), evidence('source_archive'))
    check_config(cfg, original_cfg)
    pairs = [(path, 'annotated_sha256'), (path.with_suffix('.meta.jsonl'), 'annotated_receipts_sha256'),
             (evidence('original_journal'), 'original_journal_sha256'),
             (evidence('original_receipts'), 'original_receipts_sha256'),
             (evidence('request_path'), 'request_sha256'), (Path(source_path), 'on_journal_sha256')]
    if any(sha(p) != meta[key] for p, key in pairs):
        raise ValueError('Budget annotation hash differs')
    if Path(source_path).resolve() != evidence('on_journal').resolve():
        raise ValueError('Budget annotation ON journal differs')
    old_sources, sources = _inputs(source_path, cfg, cell)
    rows, recovery = annotation_records(evidence('original_journal'))
    receipts, receipt_recovery = annotation_records(evidence('original_receipts'))
    if any(meta.get(k) != v for k, v in recovery.items()) or meta.get('receipt_recovery') != receipt_recovery:
        raise ValueError('Budget annotation recovery audit differs')
    converted, new_receipts = _convert(cfg, cell, budget, tokenizer, old_sources, sources, rows, receipts,
                                      meta['original_journal_sha256'], meta['original_receipts_sha256'])
    actual, row_audit = annotation_records(path)
    actual_receipts, receipt_audit = annotation_records(path.with_suffix('.meta.jsonl'))
    if (row_audit['skipped_line_count'] or receipt_audit['skipped_line_count'] or
            actual != converted or [r for r, _ in actual_receipts] != new_receipts):
        raise ValueError('Budget annotation changed original content')
    return meta
