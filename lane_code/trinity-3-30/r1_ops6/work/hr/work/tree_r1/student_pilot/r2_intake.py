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
from .r2_contract import validate, perception, CONTRACT
from .r2_grammar import SHARED_SHA256
from .r2_adapters import normalize
from .r2_exclusions import Exclusions, upstream
from .r2_withheld import Withheld, SHA256 as WITHHELD_SHA256


def read_rows(pin, limit):
    path = pinned(pin)
    with path.open('rb') as handle:
        header = handle.read(2)
    opener = gzip.open if header == b'\x1f\x8b' else open
    with opener(path, 'rt') as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            yield json.loads(line)


def intake(manifest_path, *, limit=2000, select_types=None):
    manifest = load(manifest_path)
    if manifest.get('schema') != 'r2-family-manifest-v1' or not manifest.get('family'):
        raise ValueError('Old-format or unnamed family manifest')
    if manifest.get('trace_contract') != CONTRACT or manifest.get('validator_sha256') != SHARED_SHA256:
        raise ValueError('Manifest contract or validator pin differs')
    remote_full = (limit is None and os.environ.get('STUDENT_R2_FRAME_HOST') == '1'
                   and os.environ.get('STUDENT_R2_LOCAL_NODE') != '1'
                   and not os.uname().nodename.startswith('trinity'))
    if not remote_full and (type(limit) is not int or not 1 <= limit <= 2000):
        raise ValueError('Local slices must contain at most 2000 rows per family')
    if manifest.get('scene_coverage') is None:
        raise ValueError('scene_coverage=None refuses; unknown overlap is not a pass')
    rule = Exclusions(manifest['exclusions'])
    merged = None
    if manifest.get('dev_scene_exclusions'):
        from .r2_scene_bindings import require_merged
        from .s1_exclusions import Exclusions as NativeExclusions
        require_merged(manifest['dev_scene_exclusions'])
        merged = NativeExclusions(manifest['dev_scene_exclusions'], manifest['exclusions']['benchmark'])
    withheld = Withheld(manifest.get('withheld_rooms'))
    from .extent_receipt import Extents
    extents = Extents(manifest.get('extent_receipt'))
    coverage = load(pinned(manifest['scene_coverage']))
    if coverage.get('exclusions') != manifest['exclusions'] or coverage.get('rows_sha256') != manifest['rows']['sha256']:
        raise ValueError('Scene coverage pins differ from this population')
    previous = upstream(manifest['upstream_receipts'], manifest['exclusions'])
    frame_map = None
    if manifest.get('frame_map'):
        if manifest.get('frame_plan'):
            from .s1_routing import Frames
            frame_map = Frames(manifest['frame_map'], manifest['frame_plan'],
                               fps_authority=manifest.get('fps_authority'))
        else:
            frame_map = load(pinned(manifest['frame_map']))
    if manifest.get('prefiltered') and not previous:
        raise ValueError('Prefiltered rows require upstream receipts')
    admitted, counts, refusals, seen = [], {}, [], set()
    for raw in read_rows(manifest['rows'], limit):
        row = raw['row'] if 'row' in raw else raw
        kind = row.get('question_type', row.get('type', manifest['stream']))
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
            extents.check(row, manifest['stream'])
            row['trace_contract'] = manifest['trace_contract']
            row['r2_envelope_sha256'] = digest(raw)
            from .r0_exclusion import reserve
            reserve().check(row, manifest['stream'])
            if manifest.get('routing_policy') == 'both-path-20261116':
                from .row_text_audit import check as check_text
                from .routing_type_gate import validate as check_form
                from .carrier_c1_routing import POLICIES
                row['routing_policy'] = manifest['routing_policy']
                check_text(row, manifest['family'])
                check_form(row, POLICIES[manifest['routing_policy']], manifest.get('artifact_heads', []))
            validate(row, manifest['stream'])
            perception(row, manifest['stream'], raw.get('target_record', {}))
            reasons = rule.check(row, coverage['rows'].get(qid))
            if withheld.touches(row, coverage['rows'].get(qid, {})):
                reasons.append('withheld_room')
            if merged is not None and merged.excluded(row):
                reasons.append('merged_dev_or_benchmark')
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
                                 family=manifest['family'], mix_cell=manifest.get('mix_cells', {}).get(qid)))
    report = dict(schema='r2-intake-report-v1', family=manifest['family'], counts=counts,
                  refusals=refusals, upstream=previous, exclusions=manifest['exclusions'],
                  manifest_path=str(manifest_path), manifest_sha256=digest(manifest),
                  slice_limit=limit, population_count=manifest['count'])
    report['withheld_rooms_sha256'] = WITHHELD_SHA256
    report['rows_withheld'] = sum('withheld_room' in r['reason'] for r in refusals)
    return admitted, report


def text_report(report):
    return f"{report['family']}: rows withheld={report['rows_withheld']}\n" + '\n'.join(f"{kind}: admitted={c['admitted']} refused={c['refused']} reasons={dict(c['reasons'])}"
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
