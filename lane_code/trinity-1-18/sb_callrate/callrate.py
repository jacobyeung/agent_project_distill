#!/usr/bin/env python3
"""Authenticated per-type call rate and response-following reader."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path
import numpy as np
from bootstrap import bootstrap
from measurements import measure, summarize
from return_reader import Inputs, DEFAULT_INPUT, OUT3, OUT3S, infer_package, load_read, registered


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a', required=True, type=Path)
    p.add_argument('--a-step', required=True, type=int)
    p.add_argument('--b', type=Path)
    p.add_argument('--b-step', type=int)
    p.add_argument('--out', required=True, type=Path)
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


def analyze(ar, ai, br, bi, sc):
    check_pair_items(ai, bi)
    a = {k: measure(r, ai[k], sc) for k, r in ar.items()}
    b = {k: measure(r, bi[k], sc) for k, r in br.items()}
    types = {}
    for kind in sorted({i['question_type'] for i in list(ai.values()) + list(bi.values())}):
        ka = {k for k,i in ai.items() if i['question_type'] == kind}
        kb = {k for k,i in bi.items() if i['question_type'] == kind}
        aa = {k:a[k] for k in sorted(ka & a.keys())}
        bb = {k:b[k] for k in sorted(kb & b.keys())}
        value = dict(a=summarize(list(aa.values()), ka), b=summarize(list(bb.values()), kb), paired=paired(aa, bb),
                     scorers=sorted({i.get('scorer', 'h1eval.scorers.accuracy') for i in list(ai.values())+list(bi.values()) if i['question_type']==kind}))
        for field in ('unit', 'wording'):
            labels = sorted({v for row in list(aa.values())+list(bb.values())
                             for v in (row[field] if field == 'wording' else [row[field]])})
            value['by_' + field] = {}
            for label in labels:
                match = lambda r: label in r[field] if field == 'wording' else r[field] == label
                sa = {k:r for k,r in aa.items() if match(r)}
                sb = {k:r for k,r in bb.items() if match(r)}
                # Trace wording is side-specific. Only shared-membership ids enter a paired stratum.
                value['by_' + field][label] = dict(a=summarize(list(sa.values()), sa),
                                                 b=summarize(list(sb.values()), sb), paired=paired(sa, sb))
        types[kind] = value
    return types, {'a': a, 'b': b}


def table(result):
    lines = ['type / stratum | n A/B | calls A/B | capped A/B | usage (eligible) A/B | answers A/B | score A/B | delta call pp [95% CI] | delta capped pp [95% CI] | delta usage pp [95% CI] | delta answer pp [95% CI] | delta score pp [95% CI]']
    def fmt(v):
        return 'MISSING' if v is None else f'{v:.6f}'
    def line(label, row):
        a,b = row['a'],row['b']
        fields = [label, f"{a['n']}/{b['n']}"]
        for key in ('call_rate', 'capped_rate'):
            fields.append(fmt(a[key])+'/'+fmt(b[key]))
        fields.append(f"{fmt(a['usage'])} ({a['usage_n']})/{fmt(b['usage'])} ({b['usage_n']})")
        for key in ('answer_rate', 'score'):
            fields.append(fmt(a[key])+'/'+fmt(b[key]))
        for metric in ('call', 'capped', 'usage', 'answer', 'score'):
            p = row['paired'][metric]
            interval = 'MISSING' if p['ci95'] is None else ', '.join(fmt(v) for v in p['ci95'])
            fields.append(f"{fmt(p['value'])} [{interval}]")
        return ' | '.join(fields)
    for kind, row in result['types'].items():
        lines.append(line(kind, row))
        for field in ('unit', 'wording'):
            for label, group in row['by_'+field].items():
                lines.append(line('  '+field+'='+label, group))
    return '\n'.join(lines)+'\n'


def execute(args, io):
    if bool(args.b) != (args.b_step is not None):
        raise ValueError('--b and --b-step must be supplied together')
    bases = args.baseline_root or io.root/OUT3/'bases'
    package = args.a_package or infer_package(io, args.a)
    sc = setup_scorer(io, args.scorer_src or Path(package)/'src')
    ar, ai, _ = load_read(io, args.a, package, args.a_read, args.a_step, bases, args.a_manifest)
    excluded = []
    if args.b:
        bpackage = args.b_package or infer_package(io, args.b)
        br, bi, _ = load_read(io, args.b, bpackage, args.b_read, args.b_step, bases, args.b_manifest)
    else:
        br, bi = registered(io, bases)
        excluded = sorted(bi.keys()-ai.keys())
        # Default comparison uses A's registered population, including b2 room ids.
        br = {k:v for k,v in br.items() if k in ai}
        bi = {k:v for k,v in bi.items() if k in ai}
        if ai.keys()-bi.keys():
            raise FileNotFoundError('MISSING: registered baseline items: ' + ', '.join(sorted(ai.keys()-bi.keys())))
    types, per_item = analyze(ar, ai, br, bi, sc)
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_relative_to(io.path(args.scorer_src or Path(package)/'src')) and Path(path).is_file():
            io.digest(path)
    result = dict(status='MISSING' if any(v[s]['status']=='MISSING' for v in types.values() for s in ('a','b')) else 'OK',
                  a_step=args.a_step, b_step=args.b_step if args.b else 544,
                  bootstrap=dict(seed=17, draws=10000, cluster='physical room', difference_units='percentage points'),
                  definitions=dict(call='At least one recorded call belonging to the item type; unserved calls count. Unrelated calls do not.',
                    capped='finish in max_calls, max_new_tokens, length; denominator is all completed items, including no-call truncation.',
                    usage='Final answer agrees with the last parsed matching response, using h1eval.scorers program_decision and answer_equals (5% relative, exact at zero); explicit units normalized; direction uses option component argmax; room uses parsed area. Denominator includes called items with a computable response decision, even without an answer.',
                    answer='A nonempty explicit answer tag or suffix after </think>; max_calls has no answer, following the scorer.',
                    score='h1eval.scorers.accuracy task_accuracy, including official EM/MRA and supplied score overrides.',
                    rates='Rates use completed items. Expected counts and missing ids are explicit; incomplete coverage is MISSING.',
                    unit='scorers.unit_factor; m/cm/ft/in/mm. N/A for non-length questions; room units refer to square units.',
                    wording='q1/classify.py overlapping TEMPL tags on distance traces with tool responses removed; otherwise question template with numbers and route object names masked. Tags can overlap; paired strata require membership on both sides.',
                    paired_usage='Paired usage delta only among ids eligible on both sides; not the difference between separately eligible marginal usage rates.'),
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
    for name in ('callrate.py', 'return_reader.py', 'measurements.py', 'wording.py', 'bootstrap.py'):
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
    print(text, file=sys.stderr, end='')
    print(data, end='')
    return 0 if result['status']=='OK' else 2


if __name__ == '__main__':
    sys.exit(main())
