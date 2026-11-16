"""Run metadata-only family proofs when the row and sealed-metadata lanes publish."""
import argparse
from pathlib import Path
from .p3_provenance import load, pinned, write
from .r2_materialize import materialize


def prove(rows_dir, sealed_meta_dir, output):
    rows_dir, sealed_meta_dir, output = Path(rows_dir), Path(sealed_meta_dir), Path(output)
    index = sealed_meta_dir/'REAL_ROW_INPUTS.json'
    if not rows_dir.is_dir() or not index.is_file():
        raise ValueError('Real-row inputs absent: require rows_dir and sealed_meta_dir/REAL_ROW_INPUTS.json; no proof was run')
    spec = load(index)
    if spec.get('schema') != 'r2-real-proof-inputs-v1' or not spec.get('expected_families'):
        raise ValueError('Real-row proof needs an explicit complete family inventory')
    manifests = [pinned(pin) for pin in spec['manifests']]
    if any(not (p.resolve().is_relative_to(rows_dir.resolve()) or p.resolve().is_relative_to(sealed_meta_dir.resolve())) for p in manifests):
        raise ValueError('Proof manifest is outside its published roots')
    values = [load(p) for p in manifests]
    if set(v['family'] for v in values) != set(spec['expected_families']):
        raise ValueError('Published family inventory is incomplete')
    if set(v['stream'] for v in values) != {'vqa', 'routing', 'pose', 'pointing'}:
        raise ValueError('Real proof requires every native stream, including both pose sources in its inventory')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for i, path in enumerate(manifests):
        report = materialize([path], output/str(i), metadata_only=True, limit=2000,
                             select_types={str(path): spec.get('select_types', {}).get(str(path))})
        if report['status'] != 'needs the frame host' or not report['missing']:
            raise ValueError('Family did not reach the frame-host boundary: ' + str(path))
        invalid = [r for rep in report['intake'] for r in rep['refusals'] if not r['reason'].startswith(('excluded:', 'lineage_less_room:', 'type_selection'))]
        if invalid:
            raise ValueError('Real family has invalid rows; inspect its intake receipt: ' + str(path))
        results.append(dict(manifest=str(path), report=report))
    result = dict(status='metadata reached frame-host boundary', rgb_read=False, results=results,
                  input_inventory=str(index), limit_per_family=2000)
    write(output/'REAL_ROW_PROOF.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rows_dir')
    parser.add_argument('sealed_meta_dir')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    prove(args.rows_dir, args.sealed_meta_dir, args.output)


if __name__ == '__main__':
    main()
