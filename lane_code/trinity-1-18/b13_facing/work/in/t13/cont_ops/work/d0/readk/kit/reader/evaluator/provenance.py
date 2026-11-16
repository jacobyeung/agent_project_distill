"""Authenticated layout annotation for completed historical runs; never for resume."""
import hashlib
import json
from pathlib import Path
from evalpath.items import digest
from journal import records, retain, annotation_records

VERSION = 'rv-annotation-3.0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def request(path, archive):
    cfg = json.loads(Path(path).read_text())
    content = {k:v for k,v in cfg.items() if k not in ('binding', 'output')}
    binding = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    if binding != cfg['binding']:
        raise ValueError('Request binding differs from recomputed content')
    if sha(archive) != cfg['source_sha256']:
        raise ValueError('Request source archive differs')
    return cfg


class Annotation:
    def __init__(self, cfg, metadata):
        self.cfg, self.metadata = cfg, metadata

    def cell(self, index):
        cell = dict(self.cfg['cells'][index])
        # These are authenticated request defaults, never values supplied by a row.
        cell.setdefault('thinking', self.cfg['thinking'])
        cell.setdefault('max_tokens', self.cfg['max_tokens'])
        cell.setdefault('decoding', 'greedy')
        return cell


def annotate(request_path, archive, original, target, cell_index):
    cfg = request(request_path, archive)
    cell = cfg['cells'][cell_index]
    binding = digest(dict(request=cfg['binding'], cell=cell_index))
    original, target = Path(original).resolve(), Path(target).resolve()
    if original == target or target.exists() or target.with_suffix('.annotation.json').exists():
        raise ValueError('Annotation requires a new output path')
    original_sha = sha(original)
    added = dict(layout_source='bound_config', original_journal_sha256=original_sha,
                 annotation_version=VERSION)
    # Validate all rows, including errors, before opening an output file.
    rows = []; complete = {}
    original_rows, recovery = annotation_records(original)
    for row, _ in original_rows:
        if row.get('binding') != binding:
            raise ValueError('Journal binding differs from recomputed bound cell')
        if 'layout' in row and row['layout'] != cell['layout']:
            raise ValueError('Historical recorded layout differs from bound cell')
        if any(k in row for k in added):
            raise ValueError('Journal is already annotated')
        retain(complete, row)
        rows.append(dict(row, layout=cell['layout'], **added))
    if sha(original) != original_sha:
        raise ValueError('Original journal changed during annotation')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False)+'\n')
    metadata = dict(version=VERSION, layout_source='bound_config',
        original_journal=preserve_input(original, target, 'original.jsonl'),
        original_journal_sha256=original_sha, annotated_sha256=sha(target),
        request_path=preserve_input(request_path, target, 'request.json'), request_sha256=sha(request_path),
        source_archive=preserve_input(archive, target, 'source.tar'), source_sha256=cfg['source_sha256'],
        cell_index=cell_index, cell_binding=binding, rows=len(rows), **recovery)
    if sha(evidence_path(target, metadata['original_journal'])) != original_sha:
        raise ValueError('Original journal changed during preservation')
    with target.with_suffix('.annotation.json').open('x') as stream:
        stream.write(json.dumps(metadata, indent=2)+'\n')
    return metadata


def preserve_input(source, target, logical_name):
    """Keep content-addressed evidence beside the copy, independent of source paths."""
    import shutil
    source, target = Path(source), Path(target)
    expected = sha(source)
    relative = Path('.annotation-inputs') / (expected + '.' + logical_name)
    saved = target.parent / relative
    saved.parent.mkdir(parents=True, exist_ok=True)
    if not saved.exists():
        with source.open('rb') as inp, saved.open('xb') as out:
            shutil.copyfileobj(inp, out, 1024 * 1024)
    if sha(saved) != expected or sha(source) != expected:
        raise ValueError('Annotation input changed during preservation')
    return relative.as_posix()


def evidence_path(path, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Annotation evidence must have a relative logical name')
    return Path(path).parent / relative


def check_config(cfg, original):
    roots = set()
    def equal(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
        if isinstance(a, str) and a.startswith('$Q/') and isinstance(b, str):
            suffix = a[2:]
            if not b.endswith(suffix):
                return False
            roots.add(b[:-len(suffix)])
            return len(roots) == 1
        return a == b
    if not equal({k:v for k,v in original.items() if k != 'output'},
                 {k:v for k,v in cfg.items() if k != 'output'}):
        raise ValueError('Annotation configuration content differs')


def verify_annotation(path, cfg, cell_index):
    path = Path(path)
    meta = json.loads(path.with_suffix('.annotation.json').read_text())
    if meta['version'] not in (VERSION, 'rv-annotation-2.0') or meta['layout_source'] != 'bound_config':
        raise ValueError('Unknown annotation protocol')
    legacy = meta['version'] == 'rv-annotation-2.0'
    def source(name):
        return Path(meta[name]) if legacy else evidence_path(path, meta[name])
    original_cfg = request(source('request_path'), source('source_archive'))
    if sha(source('request_path')) != meta['request_sha256'] or sha(path) != meta['annotated_sha256']:
        raise ValueError('Annotation file hash differs')
    if sha(source('original_journal')) != meta['original_journal_sha256']:
        raise ValueError('Original journal hash differs')
    if meta['cell_index'] != cell_index or cfg['binding'] != original_cfg['binding']:
        raise ValueError('Annotation request/cell differs')
    check_config(cfg, original_cfg)
    if legacy:
        original_rows = list(records(source('original_journal')))
    else:
        original_rows, recovery = annotation_records(source('original_journal'))
        if any(meta.get(k) != v for k,v in recovery.items()):
            raise ValueError('Annotation recovery audit differs')
    annotated_rows, annotated_recovery = annotation_records(path)
    if annotated_recovery['skipped_line_count']:
        raise ValueError('Annotation changed original content: partial annotated row')
    if len(original_rows) != len(annotated_rows):
        raise ValueError('Annotation row count differs')
    for (old,_),(new,_) in zip(original_rows,annotated_rows):
        expected = dict(old, layout=original_cfg['cells'][cell_index]['layout'],
            layout_source='bound_config',original_journal_sha256=meta['original_journal_sha256'],annotation_version=meta['version'])
        if new != expected or old.get('binding') != digest(dict(request=original_cfg['binding'],cell=cell_index)):
            raise ValueError('Annotation changed original content or binding')
    return Annotation(original_cfg, meta)
