"""python -m student_pilot.r2_intake --manifest FAMILY --output REPORT

Envelope schema and the rows-lane replacement boundary are in R2_DATA_PATH.md.
"""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import sys
from .p3_provenance import digest, load, pinned, write
from .r2_contract import validate, perception
from .r2_adapters import normalize
from .r2_exclusions import Exclusions, upstream


def read_rows(pin, limit):
    path = pinned(pin)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            yield json.loads(line)


def intake(manifest_path, *, limit=2000, select_types=None):
    manifest = load(manifest_path)
    if manifest.get('schema') != 'r2-family-manifest-v1' or not manifest.get('family'):
        raise ValueError('Old-format or unnamed family manifest')
    remote_full = (limit is None and os.environ.get('STUDENT_R2_FRAME_HOST') == '1'
                   and os.environ.get('STUDENT_R2_LOCAL_NODE') != '1'
                   and not os.uname().nodename.startswith('trinity'))
    if not remote_full and (type(limit) is not int or not 1 <= limit <= 2000):
        raise ValueError('Local slices must contain at most 2000 rows per family')
    if manifest.get('scene_coverage') is None:
        raise ValueError('scene_coverage=None refuses; unknown overlap is not a pass')
    rule = Exclusions(manifest['exclusions'])
    coverage = load(pinned(manifest['scene_coverage']))
    if coverage.get('exclusions') != manifest['exclusions'] or coverage.get('rows_sha256') != manifest['rows']['sha256']:
        raise ValueError('Scene coverage pins differ from this population')
    previous = upstream(manifest['upstream_receipts'], manifest['exclusions'])
    frame_map = load(pinned(manifest['frame_map'])) if manifest.get('frame_map') else None
    if manifest.get('prefiltered') and not previous:
        raise ValueError('Prefiltered rows require upstream receipts')
    admitted, counts, refusals, seen = [], {}, [], set()
    for raw in read_rows(manifest['rows'], limit):
        row = raw['row'] if 'row' in raw else raw
        kind = row.get('question_type', manifest['stream'])
        value = counts.setdefault(kind, dict(seen=0, admitted=0, refused=0, reasons=Counter()))
        value['seen'] += 1
        try:
            qid = row['qid']
            if qid in seen:
                raise ValueError('Duplicate QID within family')
            seen.add(qid)
            if select_types is not None and kind not in select_types:
                raise ValueError('type_selection')
            if kind == 'room_size_estimation' and not (row.get('provenance', {}).get('source_row_sha256') and row.get('provenance', {}).get('frame_indices')):
                raise ValueError('lineage_less_room: missing source-row and frame lineage')
            expected = manifest['row_bindings'].get(qid)
            if expected is None:
                raise ValueError('Missing sealed row membership')
            if digest(raw) != expected:
                raise ValueError('Stale pin or wrong scene: row differs from membership')
            row = normalize(row, frame_map)
            row['r2_envelope_sha256'] = digest(raw)
            validate(row, manifest['stream'])
            perception(row, manifest['stream'], raw.get('target_record', {}))
            reasons = rule.check(row, coverage['rows'].get(qid))
            if reasons:
                raise ValueError('excluded:' + ','.join(reasons))
        except (KeyError, TypeError, ValueError) as error:
            reason = str(error)
            value['refused'] += 1
            value['reasons'][reason] += 1
            refusals.append(dict(qid=row.get('qid'), type=kind, reason=reason))
        else:
            value['admitted'] += 1
            admitted.append(dict(row=row, target=raw.get('target_record', {}), stream=manifest['stream'],
                                 family=manifest['family']))
    report = dict(schema='r2-intake-report-v1', family=manifest['family'], counts=counts,
                  refusals=refusals, upstream=previous, exclusions=manifest['exclusions'],
                  manifest_path=str(manifest_path), manifest_sha256=digest(manifest),
                  slice_limit=limit, population_count=manifest['count'])
    return admitted, report


def text_report(report):
    return '\n'.join(f"{kind}: admitted={c['admitted']} refused={c['refused']} reasons={dict(c['reasons'])}"
                     for kind, c in sorted(report['counts'].items()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=2000)
    parser.add_argument('--select-type', action='append')
    args = parser.parse_args(argv)
    _, report = intake(args.manifest, limit=args.limit, select_types=args.select_type)
    write(Path(args.output), report)
    print(json.dumps(report, sort_keys=True))
    print(text_report(report), file=sys.stderr)
    return int(bool(report['refusals']))


if __name__ == '__main__':
    raise SystemExit(main())
