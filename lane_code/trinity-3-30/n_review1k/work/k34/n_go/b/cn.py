"""Scene census over the admitted population, computed in the kit for this leg.

The tree's census (sc/0.json, r2_scene_bindings.rebuild) counts whole stores. The pose mix reads
only the rows its source selects, and the routing build reads only its compatible training-division
base rows and the ELIGIBLE pool sources. This module recounts every census source from raw rows of
the population the stream reads, with the tree's own counters (Exclusions.expect for the independent
census, Exclusions.keep for the filter, totals to reconcile them), and never from what prepare's
filter matched. It writes:
  a.json  the census over the admitted population (schema and lists of 0.json,
          exact_rebuilt_population true), the reference the tree's coverage_report compares with
          exact equality;
  o.json  per source: whole-store census (0.json) = admitted + outside, with the row keys of every
          listed row outside the admitted population;
  3.json  2.json with scene_coverage.reference set to a.json.
Nothing here relaxes coverage_report; it only changes which population the reference counts."""
import gzip
import json
import sqlite3
from contextlib import closing
from copy import deepcopy
from pathlib import Path

VIEW = ('canonical', 'physical_group', 'room', 'alias')
POSE = {'pose_a2v3': 0, 'pose_a3v2': 1}


def view(row):
    """The fields Exclusions.identifiers and Census.identities read, nothing else."""
    out = {key: row[key] for key in ('dataset', 'scene', *VIEW) if key in row}
    for nested in ('routing', 'provenance'):
        value = row.get(nested)
        if isinstance(value, dict):
            out[nested] = {key: value[key] for key in VIEW if key in value}
        elif nested in row:
            out[nested] = value
    return out


def _sqlite(pin, with_target=False):
    from student_pilot.p3_provenance import pinned
    path = pinned(pin)
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as connection:
        query = 'SELECT i,row,target FROM rows ORDER BY i' if with_target else 'SELECT i,row FROM rows ORDER BY i'
        for item in connection.execute(query):
            yield item[0], json.loads(item[1]), (json.loads(item[2]) if with_target else None)


def _split_pose(pin, prefix):
    from student_pilot.c1_pose_mix import _row_selected
    admitted, outside = [], []
    for index, row, target in _sqlite(pin, True):
        (admitted if _row_selected(row, target, prefix) else outside).append((index, view(row)))
    return admitted, outside


def _split_whole(pin):
    from student_pilot.r2_scene_bindings import rows
    return [(index, view(row)) for index, row in enumerate(rows(pin))], []


def _routing_check(cfg, selection, legacy):
    """s1_routing._build's admitted base population: COMPATIBLE type, train scene, not held out."""
    from student_pilot.p3_provenance import load, pinned
    from student_pilot import s1_routing as R
    from student_pilot.s1_route_policy import validate as validate_policy
    from trace_format.contracts import contract_epoch
    with contract_epoch(cfg.get('contract_epoch', R.new_contracts()), heading_plane_min=cfg.get('heading_plane_min', R.heading_plane_min())):
        route_policy = validate_policy(cfg)
        pool_types = {kind for value in selection['sources'].values() if value['status'] == 'ELIGIBLE'
                      for kind, count in value['per_type'].items() if count and (
                          route_policy is None or cfg['route_table'].get(kind, 'direct') == 'route'
                          or value['kind'] == 'rows' and kind == 'route_planning')}
        check = R.compatibility(legacy['database'], legacy, pool_types)
    point = load(pinned(cfg['streams']['pointing']))
    division = load(pinned(point['division']))
    if division.get('schema') != 'diagnostic-whole-scene-division-v1' or division.get('training_only') is not True:
        raise ValueError('R1_CENSUS_DIVISION_DIFFERS')
    return check, set(division['train_scenes']), set(division['heldout_scenes']), point['division']


def _split_routing(pin, check, train, heldout):
    admitted, outside = [], []
    for index, row, _ in _sqlite(pin):
        key = row['dataset']+'/'+row['scene']
        ok = check[row['routing']['question_type']]['disposition'] == 'COMPATIBLE' and key in train and key not in heldout
        (admitted if ok else outside).append((index, view(row)))
    return admitted, outside


def _split_pool(selection):
    from student_pilot.p3_provenance import pinned
    admitted, outside = [], []
    for name, entry in sorted(selection['sources'].items()):
        target = admitted if entry['status'] == 'ELIGIBLE' else outside
        with gzip.open(pinned(entry['source']), 'rt') as stream:
            for line in stream:
                raw = json.loads(line)
                target.append(((name, raw['qid']), dict(view(raw), _pool_source=name)))
    return admitted, outside


def _count(name, items, files, pool=False):
    """Tree counters on one population: independent census (expect) and filter (keep), reconciled
    by totals(); returns (dev, test, listed row keys)."""
    from student_pilot.s1_exclusions import Exclusions, totals
    rule = Exclusions(files['dev'], files['benchmark'])
    if pool:
        sources = sorted({row['_pool_source'] for _, row in items})
        listed = []
        for source in sources:
            part = [(key, {k: v for k, v in row.items() if k != '_pool_source'}) for key, row in items if row['_pool_source'] == source]
            rule.expect(source, (row for _, row in part), dict(population='kit-admitted-census', source=source))
            for key, row in part:
                if not rule.keep(row, source):
                    listed.append([*key, *(flag for flag in rule.matches(row).values())])
    else:
        rule.expect(name, (row for _, row in items), dict(population='kit-admitted-census', source=name))
        rule.counts(name)
        listed = []
        for key, row in items:
            if not rule.keep(row, name):
                listed.append([key, *(flag for flag in rule.matches(row).values())])
    counts = totals(rule.report(), rule)
    return counts['dev_matches'], counts['benchmark_matches'], listed


def admitted(result, cfg, output, *, plant=None):
    """result: the tree's 2.json (rebuild output); cfg: the configuration rebuild ran with.
    plant (tests only): {source: key} moves that row from the outside population into the admitted one."""
    from student_pilot.p3_provenance import load, pinned, file_pin, write
    from student_pilot.r2_scene_bindings import SOURCES
    output = Path(output)
    files = result['files']
    whole = load(pinned(result['scene_coverage']['reference']))
    if whole.get('exact_rebuilt_population') is not True or whole.get('withhold_file') != files['dev']:
        raise ValueError('R1_CENSUS_WHOLE_STORE_REFERENCE_DIFFERS')
    selection = load(pinned(result['pool_selection']))
    pose = load(pinned(cfg['streams']['pose']))
    census, record, keys = {}, {}, {}
    for name in sorted(whole['withheld_training_rows']):
        entry = whole['withheld_training_rows'][name]
        if name == 'pool':
            inside, outside = _split_pool(selection)
            population = dict(rule='ELIGIBLE pool sources (s1_routing._build reads these)',
                              sources=sorted(n for n, v in selection['sources'].items() if v['status'] == 'ELIGIBLE'))
        else:
            receipt = load(pinned(result['receipts'][name]))['scene_rebuild']
            legacy = load(pinned(receipt['input_receipt']))
            if name in POSE:
                part = pose['sources'][POSE[name]]
                if part.get('receipt') != receipt['input_receipt']:
                    raise ValueError('R1_CENSUS_POSE_SOURCE_DIFFERS:'+name)
                inside, outside = _split_pose(receipt['population'], part['frame_prefix'])
                population = dict(rule='c1_pose_mix._row_selected', frame_prefix=part['frame_prefix'])
            elif SOURCES.get(name) == 'routing':
                check, train, heldout, division = _routing_check(cfg, selection, legacy)
                inside, outside = _split_routing(receipt['population'], check, train, heldout)
                population = dict(rule='s1_routing._build census_rows: COMPATIBLE, train, not held out',
                                  division=division, compatible=sorted(k for k, v in check.items() if v['disposition'] == 'COMPATIBLE'))
            else:
                inside, outside = _split_whole(receipt['population'])
                population = dict(rule='whole store (the stream build reads every row)')
            if len(inside)+len(outside) != receipt['population_count']:
                raise ValueError('R1_CENSUS_POPULATION_INCOMPLETE:'+name)
        if plant and name in plant:
            moved = [item for item in outside if item[0] == plant[name]]
            if len(moved) != 1:
                raise ValueError('R1_CENSUS_PLANT_KEY_MISSING:'+name)
            outside = [item for item in outside if item[0] != plant[name]]
            inside = inside+moved
        dev, test, listed = _count(name, inside, files, pool=(name == 'pool'))
        odev, otest, olisted = _count(name, outside, files, pool=(name == 'pool')) if outside else (0, 0, [])
        if dev+odev != entry['rows_withheld'] or test+otest != entry['benchmark_rows_withheld']:
            raise ValueError('R1_CENSUS_WHOLE_DIFFERS_FROM_ADMITTED_PLUS_OUTSIDE:'+name)
        census[name] = dict(path=entry['path'], rows_withheld=dev, benchmark_rows_withheld=test)
        record[name] = dict(population=population, admitted_rows=len(inside), outside_rows=len(outside),
                            whole=dict(dev=entry['rows_withheld'], test=entry['benchmark_rows_withheld']),
                            admitted=dict(dev=dev, test=test), outside=dict(dev=odev, test=otest),
                            outside_listed_keys=olisted)
        keys[name] = len(listed)
    receipt = dict(schema='r1-admitted-scene-census-v1', whole_store_census=result['scene_coverage']['reference'],
                   rule='whole-store census = admitted census + outside, per source and list', sources=record)
    write(output/'o.json', receipt)
    reference = dict(whole, withheld_training_rows=census, population='admitted',
                     whole_store_census=result['scene_coverage']['reference'], outside=file_pin(output/'o.json'))
    if reference['exact_rebuilt_population'] is not True:
        raise ValueError('R1_CENSUS_NOT_EXACT')
    write(output/'a.json', reference)
    bound = deepcopy(result)
    bound['scene_coverage'] = dict(result['scene_coverage'], reference=file_pin(output/'a.json'))
    bound['admitted_census'] = dict(whole=result['scene_coverage']['reference'], outside=file_pin(output/'o.json'))
    write(output/'3.json', bound)
    print(json.dumps(dict(admitted_census={n: dict(admitted=r['admitted'], outside=r['outside'], whole=r['whole'])
                                           for n, r in record.items()})), flush=True)
    return file_pin(output/'3.json')
