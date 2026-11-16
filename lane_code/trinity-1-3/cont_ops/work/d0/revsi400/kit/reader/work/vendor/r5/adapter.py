"""CPU merge extension for existing pass-3/4 bindings; reviewed kit bytes stay unchanged."""
import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from dev_scoring import installed, VERSION

PINS = {'r3':'6826c8c7e68a0fb323cf004e151af993be6336badf3027ea8465c1cdbec428ec',
        'r4':'9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def legacy(version):
    path = HERE.parent/version/'adapter.py'
    if sha(path) != PINS[version]:
        raise ValueError('Original adapter pin differs')
    spec = importlib.util.spec_from_file_location('devs1_' + version, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R3, R4 = legacy('r3'), legacy('r4')
dump, digest, jsonl = R3.dump, R3.digest, R3.jsonl
SCORERS, scoring_label = R3.SCORERS, R3.scoring_label


def original_adapter(cfg):
    for version, pin in PINS.items():
        if cfg.get('devs1', {}).get('adapter_sha256') == pin:
            return R3 if version == 'r3' else R4
    raise ValueError('Unknown original adapter binding')


def validate_request(cfg):
    request = {k:v for k,v in cfg.items() if k not in ('binding', 'output')}
    if hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest() != cfg['binding']:
        raise ValueError('Request binding differs')
    origin = original_adapter(cfg)
    if cfg.get('build_only'):
        raise ValueError('Dry bind cannot merge production journals')
    if len(cfg['cells']) != 1 or cfg['cells'][0]['benchmarks'] != ['devrows']:
        raise ValueError('Merge extension requires one dev cell')
    if cfg['devs1']['timing_version'] != R3.TIMING_VERSION:
        raise ValueError('Old timing version is void')
    cell = cfg['cells'][0]
    if origin is R3:
        origin.validate_cell(cell, cell['model'])
    else:
        origin.validate_cell(cell, cell['model'], cfg['devs1']['payload'])
    root, pins, tasks, captures = origin.payload(cfg['devs1']['payload'])
    if pins != cfg['devs1']['pins']:
        raise ValueError('Payload pins differ')
    if cfg['datasets'] != [dict(benchmark='devrows', rows=dict(path=str(root/'TASKS.jsonl'),
                                                            sha256=pins['TASKS.jsonl']))]:
        raise ValueError('Dataset differs from bound payload')
    origin.check_model_specs(cfg['models'], cell['model'])
    return origin


def checked_merges(cfg, attempt, tokenizer):
    """Call the original mergers, including prefix and budget receipt authentication."""
    with installed():
        result = kit_merge(cfg, attempt, tokenizer)
        if cfg['cells'][0]['model'] == 'cp1m200':
            importlib.import_module('budget_merge').merge_budgets(cfg, 0, attempt, tokenizer=tokenizer)
    return result


def kit_merge(cfg, attempt, tokenizer=None):
    merge = importlib.import_module('merge').merge
    options = {'tokenizer':tokenizer} if 'tokenizer' in inspect.signature(merge).parameters else {}
    return merge(cfg, 0, attempt, **options)


def merge_existing(args):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.attempt):
        raise ValueError('Unsafe attempt name')
    source, dest = Path(args.source).resolve(), Path(args.dest).resolve()
    raw_request = (source/'request.json').read_bytes()
    cfg = json.loads(raw_request)
    origin = validate_request(cfg)
    dest.mkdir(parents=True, exist_ok=False)
    (dest/'ORIGINAL_REQUEST.json').write_bytes(raw_request)
    # Reconstruct the original deterministic archive from the reviewed kit. Its hash
    # and code inventory must match the ORIGINAL request before importing any code.
    archive_sha = origin.copy_kit(args.kit, dest/'kit')
    if archive_sha != cfg['source_sha256']:
        raise ValueError('Reviewed kit differs from original source archive')
    if sha(dest/'kit/CODE_PINS.json') != cfg['devs1']['code_pins_sha256']:
        raise ValueError('Reviewed kit differs from original code inventory')
    origin.kit_import(dest/'kit')
    tokenizer = None
    if 'tokenizer' in inspect.signature(importlib.import_module('merge').merge).parameters:
        audit = importlib.import_module('token_audit')
        tokenizer = audit.load_tokenizer(cfg, directory=args.tokenizer_dir, manifest_path=args.tokenizer_manifest)
    source_dir = source/'results/0'
    names = [f'g{rank}.jsonl' for rank in range(cfg['gpus'])]
    names += [f'p{rank}_{args.attempt}.json' for rank in range(cfg['gpus'])]
    if cfg['cells'][0]['model'] == 'cp1m200':
        names += [f'budget_{budget}.g{rank}{suffix}' for budget in (2048,4096)
                  for rank in range(cfg['gpus']) for suffix in ('.jsonl','.meta.jsonl')]
    target = dest/'results/0'
    target.mkdir(parents=True)
    input_hashes = {}
    for name in names:
        path = source_dir/name
        if path.with_suffix('.annotation.json').exists():
            raise ValueError('Historical annotation bundles require their original reviewed workflow')
        raw = path.read_bytes()
        (target/name).write_bytes(raw)
        input_hashes[name] = hashlib.sha256(raw).hexdigest()
    runtime = deepcopy(cfg)
    runtime['output'] = str(dest/'results')  # Output is excluded from the request binding.
    dump(dest/'request.json', runtime)
    receipt = dict(scorer=VERSION, original_request_sha256=sha(source/'request.json'),
                   request_binding=cfg['binding'], source_sha256=archive_sha, inputs=input_hashes,
                   adapter_sha256=sha(__file__), scorer_sha256=sha(HERE/'dev_scoring.py'),
                   source=str(source), kit_source=str(Path(args.kit).resolve()),
                   tokenizer_manifest_sha256=cfg['models']['base']['manifest']['sha256'],
                   tokenizer_authenticated=tokenizer is not None,
                   tokenizer_dir=str(args.tokenizer_dir or cfg['models']['base']['path']),
                   relocation='Only output changed; request binding and original paths retained')
    dump(dest/'MERGE_INPUTS.json', receipt)
    checked_merges(runtime, args.attempt, tokenizer)
    if sha(source/'request.json') != receipt['original_request_sha256']:
        raise ValueError('Source request changed during merge')
    for name, expected in input_hashes.items():
        if sha(source_dir/name) != expected or sha(target/name) != expected:
            raise ValueError('Source or copied journal changed during merge: ' + name)
    from report import export_merged
    exports = export_merged(runtime, args.attempt, dest/'report')
    dump(dest/'MERGE_COMPLETE.json', dict(receipt_sha256=sha(dest/'MERGE_INPUTS.json'),
         exports=exports, export_sha256={arm:sha(dest/'report'/name) for arm,name in exports.items()},
         original_request_binding_unchanged=True, journals_byte_identical=True))
    print(json.dumps(dict(merged=str(dest), arms=exports, binding=cfg['binding'])))


def bind(args):
    # Binding and generation still use the exact pinned adapters and kit bytes.
    return R4.bind(args)


def launch(args):
    cfg = json.loads((Path(args.dest)/'request.json').read_text())
    origin = original_adapter(cfg)
    origin.verify_bound(args.dest)
    origin.kit_import(Path(args.dest)/'kit')
    with installed():
        return origin.launch(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    merge = sub.add_parser('merge')
    for name in ('source','dest','kit','attempt'):
        merge.add_argument('--'+name, required=True)
    merge.add_argument('--tokenizer-dir')
    merge.add_argument('--tokenizer-manifest')
    binding = sub.add_parser('bind')
    binding.add_argument('--payload','--payload-root',dest='payload',default=str(HERE.parent/'r3'))
    for name in ('kit','dest','models','frames-root'):
        binding.add_argument('--'+name,required=True)
    binding.add_argument('--cell',choices=['cp1m200','f17'],required=True)
    binding.add_argument('--dry',action='store_true')
    launch_parser = sub.add_parser('launch')
    launch_parser.add_argument('--dest',required=True)
    launch_parser.add_argument('--attempt',required=True)
    args = parser.parse_args()
    {'merge':merge_existing,'bind':bind,'launch':launch}[args.command](args)


if __name__ == '__main__':
    main()
