"""Merge disjoint D partial/remainder returns; pair only identical item IDs."""
import argparse
import json
from pathlib import Path
import score_base as base
from return_tools import unpack, load, validate_manifest
from fetch_validation import digest
from dbuild.make_items_d import subset


def records(output):
    value = output.get('calls', output.get('hook', {}))
    return value.get('records', []) if isinstance(value, dict) else value


def merge(items, parent_package, partial, remainder_items, remainder_package, remainder):
    manifest, parent = validate_manifest(items, parent_package)
    rest, child = validate_manifest(remainder_items, remainder_package)
    a, am = load(partial, items, parent_package)
    b, bm = load(remainder, remainder_items, remainder_package)
    proof = rest['remainder']
    if rest != subset(manifest, sorted(a), proof):
        raise ValueError('Remainder does not complement this partial return')
    if (proof['parent_plan'] != parent['plan'] or proof['parent_token'] != parent['token']
            or proof['parent_items_sha256'] != digest(items)
            or proof['export_binding'] != parent['export_binding']
            or child['export_binding'] != parent['export_binding']
            or child['token'] == parent['token'] or child['plan'] == parent['plan']):
        raise ValueError('Remainder provenance/export/fresh identity differs')
    # The subset validator changes; all other evaluator files must remain identical.
    if 'evaluator_files' not in parent or 'evaluator_files' not in child:
        raise ValueError('Merge requires package directories or builds with evaluator_files')
    if ({k:v for k,v in parent['evaluator_files'].items() if k != 'dist580.py'} !=
            {k:v for k,v in child['evaluator_files'].items() if k != 'dist580.py'}):
        raise ValueError('Evaluator changed beyond the subset validator')
    if ({k:v for k,v in am['binding'].items() if k != 'evaluator_code_sha256'} !=
            {k:v for k,v in bm['binding'].items() if k != 'evaluator_code_sha256'}):
        raise ValueError('Serving, export, or settings differ between segments')
    if set(a) & set(b):
        raise ValueError('Overlapping completed IDs')
    merged = dict(a)
    merged.update(b)
    result = dict(groups={n:base.metrics(merged,ks,records) for n,ks in base.groups(manifest).items()},
                  reworded_minus_twin=base.paired(merged,manifest),
                  sources=[am,bm], complete=len(merged)==manifest['count'])
    return merged, result


def score_group(spec, work):
    required = ('items','parent_package','partial_archive','partial_exit','partial_receipt',
                'remainder_items','remainder_package','remainder_archive','remainder_exit','remainder_receipt')
    if set(spec) != set(required):
        raise ValueError('Score group keys differ: '+repr(required))
    unpack(spec['partial_archive'],spec['partial_exit'],spec['partial_receipt'],spec['parent_package'],work/'partial')
    unpack(spec['remainder_archive'],spec['remainder_exit'],spec['remainder_receipt'],spec['remainder_package'],work/'remainder')
    proof = base.read(spec['remainder_items'])['remainder']
    if (proof['partial_archive_sha256'] != digest(spec['partial_archive'])
            or proof['partial_return_token'] != base.read(spec['partial_exit'])['token']):
        raise ValueError('Remainder selected from another partial archive')
    return merge(spec['items'],spec['parent_package'],work/'partial',spec['remainder_items'],
                 spec['remainder_package'],work/'remainder')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',required=True,help='JSON: current group and optional compare group; paths must be absolute')
    p.add_argument('--work',required=True,help='Fresh scratch directory')
    p.add_argument('--out',required=True)
    a = p.parse_args()
    spec = base.read(a.spec)
    if set(spec) not in ({'current'}, {'current','compare'}):
        raise ValueError('Expected current and optional compare')
    work = Path(a.work)
    work.mkdir(parents=True,exist_ok=False)
    rows, current = score_group(spec['current'],work/'current')
    result = dict(current=current,bootstrap=dict(draws=10000,seed=17,unit='room_key'),
                  call_rate_denominator='all 580 planned items',difference_units='MRA fraction')
    if 'compare' in spec:
        if digest(spec['current']['items']) != digest(spec['compare']['items']):
            raise ValueError('Comparison item manifests differ')
        other, comparison = score_group(spec['compare'],work/'compare')
        result.update(baseline=comparison,
                      step_difference=base.comparison(rows,other,base.read(spec['current']['items'])))
    with Path(a.out).open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(out=a.out,complete=current['complete'],completed=len(rows))))


if __name__ == '__main__':
    main()
