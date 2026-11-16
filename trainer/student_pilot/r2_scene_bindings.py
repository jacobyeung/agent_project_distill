"""One dev population for native selection, upstream receipts and trainer census."""
from collections import Counter
from contextlib import closing
from copy import deepcopy
import gzip
import json
import os
import sqlite3
from pathlib import Path

from .p3_provenance import encoded, file_pin, load, pinned, write, digest
from .r2_withheld import SHA256, Withheld, room
from .s1_exclusions import Exclusions, dev_names, totals

SEALED_DEV = '969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'
SOURCES = {'vqa': 'vqa', 'camera': 'routing', 'pose_a3v2': 'pose',
           'pose_a2v3': 'pose', 'pointing': 'pointing'}


def merge(dev, withheld):
    if dev['sha256'] != SEALED_DEV:
        raise ValueError('Foreign sealed dev input')
    dev_names(dev)
    Withheld(withheld)
    result, extra = deepcopy(load(pinned(dev))), load(pinned(withheld))
    rule = Exclusions(dev)
    result['rooms'] = sorted(set(result['rooms']) | {rule.key(x) for x in extra['rooms']})
    result['physical_groups'] = sorted(set(result['physical_groups']) | set(extra['rooms']))
    for room, aliases in sorted(extra['aliases'].items()):
        key = rule.key(room)
        result['aliases'][key] = sorted(set(result['aliases'].get(key, [])) | set(aliases) | {room, key})
        result['canonical'][key] = sorted(set(result['canonical'].get(key, [])) | {room})
    result['natives'] = sorted(set(result['natives']) | {a for values in extra['aliases'].values() for a in values})
    result['derivation'] = dict(sealed_dev_sha256=dev['sha256'], withheld_sha256=withheld['sha256'])
    return result


def require_merged(pin):
    expected = file_pin(Path(__file__).with_name('r2_dev_merged.json'))['sha256']
    if not pin or pin.get('sha256') != expected:
        raise ValueError('Upstream scene coverage has foreign lists or missing datasets')
    pinned(pin)


def decoded(lines):
    for index, line in enumerate(lines):
        if index >= 2000 and os.uname().nodename.startswith('trinity'):
            raise ValueError('Local metadata slices must contain at most 2000 rows per family')
        value = json.loads(line)
        yield value.get('row', value)


def rows(pin):
    path = pinned(pin)
    with path.open('rb') as handle:
        header = handle.read(16)
    if header == b'SQLite format 3\x00':
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as connection:
            yield from decoded(row[0] for row in connection.execute('SELECT row FROM rows ORDER BY i'))
    else:
        opener = gzip.open if header[:2] == b'\x1f\x8b' else open
        with opener(path, 'rt') as handle:
            yield from decoded(handle)


def rebuild_pool(manifest, dev, benchmark, output, *, remove_files=(), tokenizer=None, room_sets=None):
    """Recompute QID census lists from metadata before native pool selection."""
    from .s1_pool import Pool, prepare, ROOM_SETS
    require_merged(dev)
    original = Pool(manifest, room_sets or ROOM_SETS)
    value = deepcopy(original.manifest)
    rule = Exclusions(dev, benchmark)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    memberships = {key: set() for key in ('dev_s1', 'eval_rooms')}
    shared_counts, draw = {}, Withheld()
    population_total, final_types, pending_types = 0, Counter(), Counter()
    for source in value['sets']:
        name = source['name']
        kind = 'packed' if 'packed' in source['files'] else 'rows'
        pin = {key: source['files'][kind][key] for key in ('path', 'sha256')}
        rule.expect(name, rows(pin), pin)
        seen, listed_count, retained = 0, 0, Counter()
        excluded_counts = Counter()
        shared_counts[name] = 0
        for row in rows(pin):
            seen += 1
            matches = rule.matches(row)
            shared_counts[name] += int(any(room(name) in draw.aliases for name in rule.identifiers(row)))
            pair = (name, row['qid'])
            for key, flag in (('dev_s1', 'dev'), ('eval_rooms', 'benchmark')):
                if matches[flag]:
                    memberships[key].add(pair)
            excluded = any(matches.values()) or pair in original.lists['room_release_gate']
            excluded_counts.update(dev_s1_rows=int(matches['dev']), eval_room_rows=int(matches['benchmark']),
                                   room_release_gate_rows=int(pair in original.lists['room_release_gate']))
            listed_count += int(excluded)
            if not excluded:
                retained[row['question_type']] += 1
        if seen != source['files'][kind]['rows']:
            raise ValueError('Pool source row count differs')
        source['after_exclusions'] = dict(rows=seen-listed_count, per_type=dict(retained))
        source['exclusions'] = dict(excluded_counts)
        population_total += seen
        (final_types if source['status'] == 'final' else pending_types).update(retained)
    value['totals'] = dict(rows_in_files=population_total,
                          final_after_exclusions=dict(rows=sum(final_types.values()), per_type=dict(final_types)),
                          pending_review_after_exclusions=dict(rows=sum(pending_types.values()), per_type=dict(pending_types)))
    for key, pairs in memberships.items():
        if not original.lists[key] <= pairs:
            raise ValueError('Rebuilt pool would lose a sealed exclusion')
        path = output/(key+'.tsv')
        path.write_text(''.join(a+'\t'+b+'\n' for a, b in sorted(pairs)))
        value['exclusions'][key].update(list=str(path), list_sha256=file_pin(path)['sha256'], rows=len(pairs))
    value['exclusions']['dev_s1'].update(withhold=dev['path'], withhold_sha256=dev['sha256'])
    value['exclusions']['eval_rooms'].update(v2=benchmark['path'], v2_sha256=benchmark['sha256'])
    write(output/'0.json', value)
    report = prepare(file_pin(output/'0.json'), output/'p', remove_files, tokenizer, room_sets or ROOM_SETS, opaque=True)
    if report['blockers'] or any(str(v.get('reason', '')).startswith(('ValueError:', 'KeyError:', 'TypeError:',
            'FileNotFoundError:', 'BadGzipFile:', 'EOFError:')) for v in report['sources'].values()):
        raise ValueError('Native pool rebuild has invalid source metadata')
    totals(report['source_scene_exclusions'], rule)
    report.update(withheld_rooms_sha256=SHA256, rows_withheld_by_source=shared_counts)
    (output/'p/receipt.json').write_text(encoded(report)+'\n')
    print(json.dumps(dict(pool_rows_withheld={digest(name):count for name,count in shared_counts.items()}, receipt=file_pin(output/'p/receipt.json'))), flush=True)
    return file_pin(output/'p/receipt.json')


def rebuild_receipt(spec, dev, benchmark, output):
    """Recount a complete raw metadata population; never rewrite an old report's pin."""
    require_merged(dev)
    old = load(pinned(spec['receipt']))
    if spec['rows'] != old.get('rows_metadata', old.get('database')):
        raise ValueError('Source metadata is not bound by its input receipt')
    if old.get('count') != spec['count']:
        raise ValueError('Source metadata census differs from its input receipt')
    rule = Exclusions(dev, benchmark)
    name = spec['source']
    rule.expect(name, rows(spec['rows']), spec['rows'])
    kept, withheld = [], 0
    draw = Withheld()
    for index, row in enumerate(rows(spec['rows'])):
        withheld += int(any(room(name) in draw.aliases for name in rule.identifiers(row)))
        if rule.keep(row, name):
            kept.append(index)
    if rule.sources[name]['seen'] != spec['count']:
        raise ValueError('Source metadata census is incomplete')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'1.json', kept)
    report = rule.report()
    totals(report, rule)
    result = {'schema': 'r2-source-scene-selection-v1', 'source_scene_exclusions': report, 'count': len(kept),
              'indices': file_pin(output/'1.json'),
              'scene_rebuild': dict(input_receipt=spec['receipt'], population=spec['rows'],
                                    population_count=spec['count'], rows_withheld=withheld)}
    write(output/'0.json', result)
    print(json.dumps(dict(source=digest(name), rows_withheld=withheld, counts=rule.sources[name],
                          receipt=file_pin(output/'0.json'))), flush=True)
    return file_pin(output/'0.json')


def rebuild(spec, cfg, output):
    """Produce all scene bindings on the frame host from authenticated metadata."""
    dev, benchmark = cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions']
    require_merged(dev)
    if set(spec['sources']) != set(SOURCES):
        raise ValueError('Scene rebuild requires every stream and both pose sources')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    pool = rebuild_pool(spec['pool_manifest'], dev, benchmark, output/'p',
                        remove_files=spec.get('remove_files', ()), tokenizer=spec.get('tokenizer'))
    receipts = {name: rebuild_receipt({**value, 'source': name}, dev, benchmark, output/str(i))
                for i, (name, value) in enumerate(sorted(spec['sources'].items()))}
    reports = {name: load(pinned(pin))['source_scene_exclusions'] for name, pin in receipts.items()}
    reports['pool'] = load(pinned(pool))['source_scene_exclusions']
    census, source_map, stream_reports = {}, {}, {}
    rule = Exclusions(dev, benchmark)
    for name, report in reports.items():
        counts = totals(report, rule)
        stream = SOURCES.get(name, 'routing')
        census[name] = dict(path=(pool if name == 'pool' else receipts[name])['path'],
                            rows_withheld=counts['dev_matches'], benchmark_rows_withheld=counts['benchmark_matches'])
        source_map.setdefault(stream, []).append(dict(source=name))
        stream_reports.setdefault(stream, dict(rule.report(), upstream={}))['upstream'][name] = report
    reference = dict(schema='dev_s1_manifest_v1', withhold_file=dev, withheld_training_rows=census,
                     exact_rebuilt_population=True, benchmark_file=benchmark)
    write(output/'0.json', reference)
    removed = {name: load(pinned(pin))['scene_rebuild']['rows_withheld'] for name, pin in receipts.items()}
    removed['pool'] = sum(load(pinned(pool))['rows_withheld_by_source'].values())
    result = dict(pool_selection=pool, receipts=receipts, reports=stream_reports, rows_withheld=removed,
                  scene_coverage=dict(schema='s1-scene-coverage-v1', reference=file_pin(output/'0.json'),
                                      source_map=source_map), files=rule.files)
    write(output/'2.json', result)
    return result


def verify(cfg):
    """Trainer checks the same merged population and all re-derived upstream pins."""
    if cfg.get('r2_identity') and not cfg.get('r2_all_stream_exclusions'):
        raise ValueError('Scene exclusion binding differs')
    if not cfg.get('r2_all_stream_exclusions'):
        return
    require_merged(cfg.get('dev_scene_exclusions'))
    value = load(pinned(cfg['r2_scene_rebuild']))
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    if value['files'] != rule.files or value['scene_coverage'] != cfg.get('scene_coverage'):
        raise ValueError('Scene exclusion binding differs')
    if set(value['receipts']) != set(SOURCES) or set(value['reports']) != set(SOURCES.values()):
        raise ValueError('Scene rebuild requires every stream and both pose sources')
    totals(load(pinned(value['pool_selection']))['source_scene_exclusions'], rule)
    for pin in value['receipts'].values():
        totals(load(pinned(pin))['source_scene_exclusions'], rule)
    for report in value['reports'].values():
        totals(report, rule)
    reference = load(pinned(cfg['scene_coverage']['reference']))
    if reference.get('withhold_file') != rule.files['dev']:
        raise ValueError('Independent scene census uses a different withheld population')
    if reference.get('exact_rebuilt_population') is not True or reference.get('benchmark_file') != rule.files['benchmark']:
        raise ValueError('Independent scene census uses a different withheld population')
    if cfg.get('r2_build2'):
        counts = load(pinned(cfg['r2_build2']['counts']))
        if counts.get('merged_dev') != rule.files['dev'] or cfg['r2_sampling']['counts'] != cfg['r2_build2']['counts']:
            raise ValueError('Host counts differ from the admitted mixture')


def populations(manifests, cfg, result, output, *, full=False):
    """Count actual admitted envelopes in final store order, before any RGB IO."""
    from .r2_intake import intake
    from .r2_mix import validate_table
    from .r2_exclusions import SEALED
    from .r2_portable import bound
    mix_pin = cfg['r2_build2']['mix']
    mix = validate_table(load(bound(mix_pin)))
    stream_for = {c['type']: c['stream'] for c in mix['cells']}
    cells, indices = Counter(), {key: [] for key in stream_for}
    offsets, pairs, seen, family_rows = Counter(), {}, set(), Counter()
    receipts, rebound = [], []
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    allowed = {}
    for source, pin in result['receipts'].items():
        receipt = load(pinned(pin))
        selected = set(load(pinned(receipt['indices'])))
        allowed[source] = {row['qid'] for i, row in enumerate(rows(receipt['scene_rebuild']['population'])) if i in selected}
    selection = load(pinned(result['pool_selection']))
    allowed['pool'] = set()
    for source in selection['sources'].values():
        if source['status'] == 'ELIGIBLE':
            selected = set(load(pinned(source['selection'])))
            allowed['pool'].update(row['qid'] for i, row in enumerate(rows(source['source'])) if i in selected)
    for number, manifest in enumerate(manifests):
        value = load(manifest)
        source = value['scene_source']
        if source not in allowed or (source != 'pool' and SOURCES[source] != value['stream']):
            raise ValueError('Family has an unknown scene source')
        value['dev_scene_exclusions'] = cfg['dev_scene_exclusions']
        path = Path(output)/(str(number)+'m.json')
        write(path, value)
        rebound.append(path)
        accepted, report = intake(path, limit=None if full else 2000)
        seen_count = sum(v['seen'] for v in report['counts'].values())
        family_rows[value['family']] += seen_count
        if seen_count != value['count'] or (not full and family_rows[value['family']] > 2000):
            raise ValueError('Metadata counts require a complete bounded family')
        if any(not r['reason'].startswith(('excluded:', 'lineage_less_room:')) for r in report['refusals']):
            raise ValueError('Metadata intake refused invalid rows')
        counts = Counter()
        for item in accepted:
            row, stream = item['row'], item['stream']
            qid = row['qid']
            original = row.get('provenance', {}).get('source_qid', qid)
            if qid in seen or original not in allowed[source] or rule.excluded(row):
                raise ValueError('Admitted family differs from rebuilt source selection')
            seen.add(qid)
            assignment = value['mix_cells'][qid]
            kind = assignment['type']
            if stream_for.get(kind) != stream:
                raise ValueError('Metadata type assignment crosses streams')
            index = offsets[stream]
            offsets[stream] += 1
            if kind == 'facing_pairs':
                pairs.setdefault(assignment['pair'], []).append(index)
            else:
                indices[kind].append(index)
            counts[kind] += 1
        cells.update(counts)
        receipt = dict(schema='r2-filtered-population-v1', complete=True, exclusions=SEALED,
                       withheld_sha256=SHA256, cells=dict(counts), merged_dev=cfg['dev_scene_exclusions'],
                       intake=report, manifest=file_pin(path))
        pin = Path(output)/(str(number)+'c.json')
        write(pin, receipt)
        receipts.append(file_pin(pin))
    if any(len(pair) != 2 for pair in pairs.values()):
        raise ValueError('Withholding leaves an incomplete facing pair')
    indices['facing_pairs'] = list(pairs.values())
    counts_path = Path(output)/'c.json'
    write(counts_path, dict(schema='r2-filtered-counts-v1', after_filtering=True,
                           mix_sha256=mix_pin['sha256'], receipts=receipts, cells=dict(cells),
                           merged_dev=cfg['dev_scene_exclusions']))
    index_path = Path(output)/'i.json'
    write(index_path, dict(schema='r2-type-indices-v1', counts_sha256=file_pin(counts_path)['sha256'], cells=indices))
    return rebound, file_pin(counts_path), file_pin(index_path)


def prepare_host(root, packet, cfg, manifests, *, full=False):
    if not packet.get('scene_rebuild'):
        raise ValueError('Missing all-stream scene rebuild inputs')
    cfg = deepcopy(cfg)
    for key in ('dev_scene_exclusions', 'benchmark_scene_exclusions'):
        pin = cfg[key]
        cfg[key] = {**pin, 'path': str(Path(root)/pin['path'])}
    require_merged(cfg['dev_scene_exclusions'])
    output = Path(root)/packet['output']/'s'
    if not output.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Scene output escapes job root')
    if output.parent.exists():
        raise ValueError('Job output must be a new folder inside its job root')
    spec = load(pinned(packet['scene_rebuild']))
    if full and {spec['sources'][name]['rows']['sha256'] for name in ('pose_a3v2', 'pose_a2v3')} != {
            pin['sha256'] for pin in packet['pose_sources']}:
        raise ValueError('Pose sources differ from the sealed source pins')
    result = rebuild(spec, cfg, output)
    cfg['scene_coverage'] = result['scene_coverage']
    cfg['r2_scene_rebuild'] = file_pin(output/'2.json')
    # Portable mixture pins are resolved once; generated receipts stay inside the job.
    from .r2_portable import bound
    cfg['r2_build2']['mix'] = file_pin(bound(cfg['r2_build2']['mix'], root))
    rebound, counts, indices = populations(manifests, cfg, result, output, full=full)
    cfg['r2_build2']['counts'] = counts
    cfg['r2_sampling'] = dict(mix=cfg['r2_build2']['mix'], counts=counts, indices=indices)
    verify(cfg)
    return cfg, rebound, dict(receipt=cfg['r2_scene_rebuild'], counts=counts, indices=indices)
