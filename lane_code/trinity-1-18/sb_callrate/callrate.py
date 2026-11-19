#!/usr/bin/env python3
"""Authenticated per-type call rate and response-following reader."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path
import numpy as np
from bootstrap import bootstrap
from measurements import measure, summarize, unit
from populations import ROOM, tag_items, inherit_tags, room_mra
from return_reader import Inputs, DEFAULT_INPUT, OUT3, OUT3S, infer_package, load_read, registered


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a', required=True, type=Path)
    p.add_argument('--a-step', required=True, type=int)
    p.add_argument('--b', type=Path)
    p.add_argument('--b-step', type=int)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--summary', action='store_true', help='Print only the compact RESULT summary to stdout; retain full output files')
    p.add_argument('--allow-partial', action='store_true', help='Permit labelled incomplete coverage')
    p.add_argument('--allow-subset', action='store_true', help='Compare shared IDs only; print original set sizes')
    p.add_argument('--strata', type=Path, help='JSON item ID to stratum label and unit')
    p.add_argument('--input-root', type=Path, default=DEFAULT_INPUT, help='Copied input tree for defaults and absolute symlink relocation')
    p.add_argument('--original-root', default='/scratch/jjyeung/orch_n30', help='Original prefix of copied absolute symlinks')
    p.add_argument('--baseline-root', type=Path, help='Registered b1/b2 packages and authenticated returns')
    p.add_argument('--a-package', type=Path, help='A package with READ_PLAN.json, tower_sequence.py, package/0.json and src/')
    p.add_argument('--b-package', type=Path)
    p.add_argument('--a-read', type=int, default=0)
    p.add_argument('--b-read', type=int, default=0)
    p.add_argument('--a-manifest', type=Path)
    p.add_argument('--b-manifest', type=Path)
    p.add_argument('--scorer-src', type=Path, help='Package src containing h1eval/ and tree/')
    return p


def setup_scorer(io, source):
    source = io.path(source)
    for file in ('h1eval/scorers.py', 'rows/expected_calls.py', 'tree/evalpath/run.py',
                 'tree/evalpath/official.py', 'tree/trace_format/room_v314.py'):
        io.digest(source/file)
    sys.path[:0] = [str(source), str(source/'tree'), str(source/'b')]
    from h1eval import scorers
    if Path(scorers.__file__).resolve() != (source/'h1eval/scorers.py').resolve():
        raise ValueError('Scorer already imported from another package; run comparisons in separate processes')
    return scorers


def paired(a, b):
    shared = sorted(a.keys() & b.keys())
    result = {'n': len(shared), 'a_only_ids': sorted(a.keys()-b.keys()), 'b_only_ids': sorted(b.keys()-a.keys())}
    for name in ('call', 'capped', 'answer', 'score', 'usage'):
        pairs = [(a[k]['room'], 100*(a[k][name]-b[k][name])) for k in shared
                 if a[k][name] is not None and b[k][name] is not None]
        result[name] = bootstrap(pairs)
        result[name]['status'] = 'OK' if pairs else 'MISSING'
    return result


def check_pair_items(a, b):
    for key in a.keys() & b.keys():
        for field in ('question_type', 'room_key', 'question', 'ground_truth', 'options'):
            if a[key].get(field) != b[key].get(field):
                raise ValueError('Paired item differs: ' + key + '/' + field)


def analyze(ar, ai, br, bi, sc, allow_subset=False, strata=None):
    check_pair_items(ai, bi)
    a = {k: measure(r, ai[k], sc) for k, r in ar.items()}
    b = {k: measure(r, bi[k], sc) for k, r in br.items()}
    types, selected = {}, {'a': {}, 'b': {}}
    for kind in sorted({i['question_type'] for i in list(ai.values()) + list(bi.values())}):
        ka = {k for k,i in ai.items() if i['question_type'] == kind}
        kb = {k for k,i in bi.items() if i['question_type'] == kind}
        ra, rb = ka & a.keys(), kb & b.keys()
        if (ka != kb or ra != rb) and not allow_subset:
            raise ValueError(f'ID sets differ for {kind}: planned A={len(ka)} B={len(kb)}, completed A={len(ra)} B={len(rb)}; use --allow-subset')
        shared, expected = ra & rb, ka & kb
        aa = {k:a[k] for k in sorted(shared)}
        bb = {k:b[k] for k in sorted(shared)}
        selected['a'].update(aa); selected['b'].update(bb)
        def group(ids):
            sa = {k:r for k,r in aa.items() if k in ids}
            sb = {k:r for k,r in bb.items() if k in ids}
            return dict(a=summarize(list(sa.values()), ids), b=summarize(list(sb.values()), ids), paired=paired(sa, sb))
        value = group(expected)
        value['set_sizes'] = dict(a=len(ka), b=len(kb), completed_a=len(ra), completed_b=len(rb), shared=len(shared))
        value['coverage'] = dict(a=summarize([a[k] for k in sorted(ra)], ka), b=summarize([b[k] for k in sorted(rb)], kb))
        value['source_reads'] = {side: sorted({items[k].get('_source_read', 'MISSING') for k in ids})
                                 for side, items, ids in [('a',ai,ka),('b',bi,kb)]}
        value['scorers'] = sorted({i.get('scorer', 'h1eval.scorers.accuracy') for i in list(ai.values())+list(bi.values()) if i['question_type']==kind})
        # Unit groups derive from questions, including missing journal rows.
        units = {k:unit(ai[k], sc) for k in expected}
        value['by_unit'] = {label:group({k for k,u in units.items() if u == label}) for label in sorted(set(units.values()))}
        value['by_wording'] = {}
        for label in sorted({v for row in list(aa.values())+list(bb.values()) for v in row['wording']}):
            # Trace tags are diagnostics; both marginals use shared membership.
            ids = {k for k in shared if label in aa[k]['wording'] and label in bb[k]['wording']}
            value['by_wording'][label] = group(ids)
        value['by_stratum'], value['by_stratum_unit'] = {}, {}
        if strata is not None and (ka | kb) & strata.keys():
            tags = {k:strata.get(k, {'stratum':'MISSING', 'unit':units[k]}) for k in expected}
            for label in sorted({v['stratum'] for v in tags.values()}):
                ids = {k for k,v in tags.items() if v['stratum'] == label}
                value['by_stratum'][label] = group(ids)
                value['by_stratum_unit'][label] = {u:group({k for k in ids if tags[k]['unit'] == u})
                                                  for u in sorted({tags[k]['unit'] for k in ids})}
        types[kind] = value
    return types, selected


def coverage_text(row):
    a,b = row['a'],row['b']
    return f"{a['n']}/{a['expected']} / {b['n']}/{b['expected']}"


def source_text(row):
    reads = row.get('source_reads', {})
    return 'A=' + ','.join(reads.get('a', ['MISSING'])) + '; B=' + ','.join(reads.get('b', ['MISSING']))


def output_rows(result, include_wording=False):
    for kind, row in result['types'].items():
        label = kind + (' ['+source_text(row)+']' if kind == ROOM else '')
        yield label, row
        fields = ('unit', 'wording') if include_wording else (('unit',) if kind == 'object_abs_distance' else ())
        for field in fields:
            for label, group in row['by_'+field].items():
                yield kind+' '+field+'='+label+(' ['+source_text(row)+']' if kind == ROOM else ''), group
        for label, group in row['by_stratum'].items():
            yield kind+' stratum='+label+(' ['+source_text(row)+']' if kind == ROOM else ''), group
            for u, subgroup in row['by_stratum_unit'][label].items():
                yield kind+' stratum='+label+' unit='+u+(' ['+source_text(row)+']' if kind == ROOM else ''), subgroup
    if result.get('room_secondary'):
        row = result['room_secondary']
        yield 'room36 secondary ['+source_text(row)+']', row


def table(result):
    lines = banners(result) + ['type / stratum | n/expected A / B | calls A/B | capped A/B | usage A/B | follow_converted A/B | copied_unconverted A/B | other A/B | conversion_failure A/B | answers A/B | not_seen A/B | other_non_numeric A/B | score/MRA A/B | delta call pp [95% CI] | delta capped pp [95% CI] | delta usage pp [95% CI] | delta answer pp [95% CI] | delta score pp [95% CI]']
    fmt = lambda v: 'MISSING' if v is None else f'{v:.6f}'
    for label, row in output_rows(result, include_wording=True):
        fields = [label, coverage_text(row)]
        for key in ('call_rate', 'capped_rate', 'usage', 'follow_converted', 'copied_unconverted', 'other', 'conversion_failure', 'answer_rate', 'not_seen_rate', 'other_non_numeric_rate', 'score'):
            fields.append(fmt(row['a'][key])+'/'+fmt(row['b'][key]))
        fields += [delta_text(row['paired'][m]) for m in ('call', 'capped', 'usage', 'answer', 'score')]
        lines.append(' | '.join(fields))
    lines.extend(room_summary(result))
    return '\n'.join(lines)+'\n'


def banners(result):
    lines = []
    if result.get('partial'):
        lines.append('PARTIAL: incomplete return coverage; all comparisons use shared completed IDs.')
    for kind,row in result['types'].items():
        sizes = row['set_sizes']
        if result.get('allow_subset') or sizes['a'] != sizes['b'] or sizes['completed_a'] != sizes['completed_b']:
            lines.append(f"SETS {kind}: planned A={sizes['a']} B={sizes['b']}; completed A={sizes['completed_a']} B={sizes['completed_b']}; shared={sizes['shared']}; coverage " + coverage_text(row['coverage']))
    return lines


def percent(value):
    return 'MISSING' if value is None else f'{100*value:.2f}'


def delta_text(p):
    value = 'MISSING' if p['value'] is None else f"{p['value']:.2f}"
    ci = 'MISSING' if p['ci95'] is None else ', '.join(f'{v:.2f}' for v in p['ci95'])
    return f'{value} [{ci}]'


def room_summary(result):
    if not result.get('room_mra'):
        return []
    reads = source_text(result['types'][ROOM])
    lines = ['room population [source read A/B] | n/expected A / B | MRA answer % A/B | delta A-B pp [95% CI]']
    for label, row in result['room_mra'].items():
        a, b = row['a'], row['b']
        lines.append(f"{label} [{reads}] | {coverage_text(row)} | {percent(a['mra_answer'])}/{percent(b['mra_answer'])} | {delta_text(row['paired'])}")
    return lines


def summary(result):
    lines = banners(result) + [f"A={result['a_step']} B={result['b_step']}; rates/scores in %, delta A-B in pp",
             'type / stratum | n/expected A / B | call A/B | capped A/B | usage A/B | follow_converted A/B | copied_unconverted A/B | other A/B | conversion_failure A/B | answer A/B | not_seen A/B | other_non_numeric A/B | score/MRA A/B | delta call [95% CI] | delta score [95% CI]']
    for label,row in output_rows(result):
        values = [percent(row['a'][key])+'/'+percent(row['b'][key])
                  for key in ('call_rate', 'capped_rate', 'usage', 'follow_converted', 'copied_unconverted', 'other', 'conversion_failure', 'answer_rate', 'not_seen_rate', 'other_non_numeric_rate', 'score')]
        lines.append(' | '.join([label, coverage_text(row), *values, delta_text(row['paired']['call']), delta_text(row['paired']['score'])]))
    lines.extend(room_summary(result))
    return '\n'.join(lines)+'\n'


def read_strata(io, path, items, sc):
    if path is None:
        return None
    data = io.read(path)
    if not isinstance(data, dict):
        raise ValueError('--strata must be an item-ID mapping')
    result = {}
    for key, value in data.items():
        if key == '_meta':
            continue
        if not isinstance(value, dict) or not isinstance(value.get('stratum'), str) or not value['stratum'].strip() or not isinstance(value.get('unit'), str):
            raise ValueError('Invalid stratum/unit for '+key)
        if key in items and value['unit'] != unit(items[key], sc):
            raise ValueError('Strata unit differs from question for '+key)
        result[key] = value
    if not result.keys() & items.keys():
        raise ValueError('MISSING: --strata contains no IDs in the requested reads: '+str(path))
    return result


def execute(args, io):
    if bool(args.b) != (args.b_step is not None):
        raise ValueError('--b and --b-step must be supplied together')
    bases = args.baseline_root or io.root/OUT3/'bases'
    package = args.a_package or infer_package(io, args.a)
    sc = setup_scorer(io, args.scorer_src or Path(package)/'src')
    ar, ai, _ = load_read(io, args.a, package, args.a_read, args.a_step, bases, args.a_manifest)
    excluded = []
    secondary = None
    five_type = len({i['question_type'] for i in ai.values()}) == 5 and any(i['question_type'] == ROOM for i in ai.values())
    if args.b:
        bpackage = args.b_package or infer_package(io, args.b)
        br, bi, _ = load_read(io, args.b, bpackage, args.b_read, args.b_step, bases, args.b_manifest)
    else:
        br, bi = registered(io, bases, room_baseline='b1' if five_type else 'b2')
        excluded = sorted(bi.keys()-ai.keys())
        # Default comparison uses A's registered population.
        br = {k:v for k,v in br.items() if k in ai}
        bi = {k:v for k,v in bi.items() if k in ai}
        if ai.keys()-bi.keys():
            raise FileNotFoundError('MISSING: registered baseline items: ' + ', '.join(sorted(ai.keys()-bi.keys())))
    inherit_tags(ai, bi, check_pair_items)
    inherit_tags(bi, ai, check_pair_items)
    untagged = lambda: [k for items in (ai, bi) for k,i in items.items()
                        if i['question_type'] == ROOM and not i.get('_population')]
    population_manifest = io.path(bases/'b2/src/items/room134.json')
    if untagged() and population_manifest.is_file():
        catalog = tag_items(io.read(population_manifest))
        inherit_tags(ai, catalog, check_pair_items)
        inherit_tags(bi, catalog, check_pair_items)
    missing_population_ids = sorted(set(untagged()))
    partial = ar.keys() != ai.keys() or br.keys() != bi.keys()
    if args.summary and partial and not args.allow_partial:
        raise ValueError('PARTIAL: incomplete return coverage; --summary requires --allow-partial (and --allow-subset if A/B IDs differ)')
    strata = read_strata(io, args.strata, {**bi, **ai}, sc)
    types, per_item = analyze(ar, ai, br, bi, sc, args.allow_subset, strata)
    if not args.b and five_type:
        sr, si, _ = load_read(io, bases/'b2/work/ret', bases/'b2', 0, 544, bases)
        room_ids = {k for k,i in ai.items() if i['question_type'] == ROOM}
        secondary_types, _ = analyze({k:r for k,r in ar.items() if k in room_ids},
            {k:i for k,i in ai.items() if k in room_ids}, {k:r for k,r in sr.items() if k in room_ids},
            {k:i for k,i in si.items() if k in room_ids}, sc, args.allow_subset)
        secondary = secondary_types[ROOM]
    # Population marginals use exactly the same shared IDs as type comparisons.
    shared_items = {side:{k:i for k,i in items.items() if k in ai.keys() & bi.keys()}
                    for side,items in [('a',ai),('b',bi)]}
    missing_strata = sorted(k for kind,v in types.items() if 'MISSING' in v['by_stratum']
                            for k,i in shared_items['a'].items() if i['question_type'] == kind and k not in strata)

    for side, items in (('a', ai), ('b', bi)):
        for key, value in per_item[side].items():
            if items[key]['question_type'] == ROOM:
                value['population'] = items[key].get('_population') or 'MISSING'
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_relative_to(io.path(args.scorer_src or Path(package)/'src')) and Path(path).is_file():
            io.digest(path)
    result = dict(status='MISSING' if missing_population_ids or missing_strata else ('PARTIAL' if partial else 'OK'),
                  partial=partial, allow_partial=args.allow_partial, allow_subset=args.allow_subset,
                  room_secondary=secondary, missing_strata_ids=missing_strata,
                  strata_unused_ids=sorted(strata.keys() - (ai.keys() | bi.keys())) if strata is not None else [],
                  a_step=args.a_step, b_step=args.b_step if args.b else 544,
                  bootstrap=dict(seed=17, draws=10000, cluster='physical room', difference_units='percentage points'),
                  definitions=dict(call='At least one recorded call belonging to the item type; unserved calls count. Unrelated calls do not.',
                    capped='finish in max_calls, max_new_tokens, length; denominator is all completed items, including no-call truncation.',
                    usage='Answer follows the response: follow_converted + copied_unconverted. Three exclusive categories use scorer tolerance (5%, exact zero). Converted agreement takes precedence at zero. Categories and usage divide by parsed response eligibility; missing answers are other. conversion_failure is copied_unconverted divided by eligible non-metre questions (square units for rooms).',
                    answer='Final answer parses as a finite value using the scorer numeric parser or as a listed option. not_seen and other_non_numeric have separate rates over completed items. max_calls suppresses answers.',
                    score='h1eval.scorers.accuracy task_accuracy, including official EM/MRA and supplied score overrides.',
                    room_mra='mra_answer equals the room answer score on [0,1], averaged over completed items including unanswered/capped items, not conditioned on answer presence. Population comes from explicit manifest sets/tags or an identity-checked join to the registered room134 manifest. Summary displays MRA in percent.',
                    rates='Marginals and deltas use shared completed IDs; n/expected and original planned/completed set sizes are explicit. Incomplete coverage is PARTIAL.',
                    unit='scorers.unit_factor; m/cm/ft/in/mm. N/A for non-length questions; room units refer to square units.',
                    wording='Trace-derived diagnostics, not question-wording effects: q1/classify.py overlapping tags with tool responses removed; otherwise masked question templates. Both marginals and deltas use shared tag membership.',
                    strata='External item-ID mapping fixes membership across sides, independent of the current output. Per-stratum and stratum-by-unit score/MRA and call rows use shared IDs. Missing labels within a represented type say MISSING; units must match the question.',
                    paired_usage='Paired usage delta only among ids eligible on both sides; not the difference between separately eligible marginal usage rates.'),
                  room_mra=room_mra(per_item, shared_items),
                  population_status='MISSING' if missing_population_ids else 'OK',
                  missing_population_ids=missing_population_ids,
                  population_error=(f'MISSING: explicit population membership for {missing_population_ids} in authenticated item manifests or {population_manifest}' if missing_population_ids else None),
                  default_baseline_excluded_ids=excluded, types=types, per_item=per_item,
                  runtime=dict(python=sys.version.split()[0], numpy=np.__version__))
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    io = Inputs(args.input_root, args.original_root)
    # Output must never be placed within returns, packages, or the copied inputs.
    protected = [args.input_root, args.a, args.b, args.a_package, args.b_package, args.baseline_root, args.scorer_src]
    target = args.out.resolve()
    if any(p and target.is_relative_to(io.path(p).resolve()) for p in protected):
        raise ValueError('--out must be outside every input directory')
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ('callrate.py', 'return_reader.py', 'measurements.py', 'wording.py', 'bootstrap.py', 'populations.py'):
        io.digest(Path(__file__).parent/name)
    try:
        result = execute(args, io)
    except (ValueError, KeyError, IndexError, FileNotFoundError, ImportError) as exc:
        result = dict(status='MISSING' if isinstance(exc, (FileNotFoundError, ImportError)) else 'INVALID', error=str(exc))
    result['command'] = [sys.executable, str(Path(__file__).absolute()), *(sys.argv[1:] if argv is None else argv)]
    result['sources'] = io.provenance()
    result['relocated_links'] = io.links
    data = json.dumps(result, indent=2, allow_nan=False)+'\n'
    (args.out/'callrate.json').write_text(data)
    if 'types' in result:
        text = table(result)
    else:
        text = result['status']+': '+result['error']+'\n'
    (args.out/'callrate.txt').write_text(text)
    if args.summary:
        if 'types' not in result:
            print(result['error'].replace('\n', ' '), file=sys.stderr)
            (args.out/'callrate.summary.txt').write_text(text)
            return 2
        compact = summary(result) if 'types' in result else text
        (args.out/'callrate.summary.txt').write_text(compact)
        print(compact, end='')
        if result.get('population_error'):
            print(result['population_error'], file=sys.stderr)
    else:
        print(text, file=sys.stderr, end='')
        print(data, end='')
    return 0 if result['status']=='OK' or (result['status']=='PARTIAL' and args.allow_partial) else 2


if __name__ == '__main__':
    sys.exit(main())
