"""EAT-1 runner: wraps any reader with one `generate(frames, question)` entry and judges clauses A1-A6.

Reader protocol (what a reader must expose):
  reader.model              torch module; heads, towers and call handlers are registered under it
  reader.tokenizer          .decode(ids) -> str
  reader.artifact_manifest  path of the eat1-artifact-v1 manifest (artifact.py)
  reader.generate(frames, question) -> dict(text, answer, calls=[dict(call, response, fields)])
      `fields` maps each response field to the list of module names (manifest `name`) behind it.
  optional reader.lm()      the module whose forward takes input_ids and returns logits
                            (default: the manifest module with role lm)
  optional reader.eat1_cache_proof  path of a cache equality proof (A5 iii)
Decoding is greedy, batch size 1.

Usage:
  python -m eat1.run --reader pkg.mod:factory --reader-kwargs '{...}' --items items.jsonl --out DIR
         [--input-root DIR ...] [--code-root DIR ...] [--sandbox] [--perturb] [--strace-log LOG]
"""
import argparse
import copy
import importlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from . import hook as H
from . import scan as S
from .artifact import Artifact, MODEL_ROLES

EAT1_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------- loading
def load_reader(spec, kwargs):
    module, _, factory = spec.partition(':')
    return getattr(importlib.import_module(module), factory)(**kwargs)


def lm_module(reader, declared):
    if hasattr(reader, 'lm'):
        return reader.lm()
    lms = [m for _, m, role, _ in declared if role == 'lm']
    if len(lms) != 1:
        raise ValueError('declare exactly one lm module or expose reader.lm()')
    return lms[0]


def read_items(path, limit=None):
    items = [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    return items[:limit] if limit else items


# ---------------------------------------------------------------- observation
def observe(reader, items, artifact, trace_lines=True, audit=True, monitor=True):
    declared = artifact.module_roles(reader.model)
    scope = H.LineScope() if trace_lines else None
    mon = H.ModelMonitor(reader.model, lm_module(reader, declared), declared, scope) if monitor else None
    opener = H.open_audit() if audit else None
    records = []
    if scope:
        scope.start()
        scope.pause()
    try:
        for index, item in enumerate(items):
            maps0 = H.mapped_files() if audit else set()
            if opener:
                opener.take()
            H.marker('start', index)
            if mon:
                mon.begin()
            if scope:
                scope.resume()
            if opener:
                opener.active = True
            t0 = time.perf_counter()
            error = None
            try:
                output = reader.generate(item['frames'], item['question'])
            except Exception as exc:  # recorded as a failure of the item, never substituted
                output, error = dict(text='', answer=None, calls=[]), f'{type(exc).__name__}: {exc}'
            seconds = time.perf_counter()-t0
            if opener:
                opener.active = False
            if scope:
                scope.pause()
            events = mon.end() if mon else []
            H.marker('end', index)
            opens = opener.take() if opener else []
            maps = sorted(H.mapped_files()-maps0) if audit else []
            prov = H.provenance(events) if mon else None
            generated_text = reader.tokenizer.decode(prov['generated']) if prov else None
            records.append(dict(id=item.get('id', str(index)), type=item.get('type', 'all'), seconds=seconds,
                                error=error, output=_jsonable(output), provenance=prov,
                                generated_text=generated_text, opens=opens, mapped=maps))
    finally:
        lines = scope.stop() if scope else None
        if mon:
            mon.close()
    return records, lines, declared


def _jsonable(output):
    return json.loads(json.dumps(output, default=str))


# ---------------------------------------------------------------- clauses
def clause(status, summary, offenders=(), **extra):
    return dict(status=status, summary=summary, offenders=list(offenders), **extra)


def judge_a1(records, artifact, input_roots, strace=None):
    recs = []
    for r in records:
        recs += [tuple(o) for o in r['opens'] if o[0] == 'open']
        recs += [('mmap', p, False) for p in r['mapped']]
    if strace:
        recs += [('strace', p, w) for _, p, w in strace]
    cats = H.classify_files(recs, artifact, input_roots)
    offenders = [dict(file=o['path'], sha256=o['sha256'], source=o['source'], opened_at=o.get('opened_at'))
                 for o in cats['outside_data']]
    status = 'FAIL' if offenders else 'PASS'
    return clause(status, f'{len(cats["artifact"])} artifact, {len(cats["code"])} code, '
                          f'{len(cats["input"])} input, {len(offenders)} outside-artifact data files opened '
                          f'after generate() started', offenders,
                  code_files=cats['code'], artifact_files=cats['artifact'],
                  environment_files=len(cats['environment']), strace=strace is not None)


def judge_a2(records, declared, findings=(), dynamic=True):
    offenders, entries = [], Counter()
    handlers = [n for _, _, role, n in declared if role == 'call_handler']
    for r in records:
        p = r['provenance']
        entries[p['entries']] += 1
        if p['entries'] != 1:
            offenders.append(dict(item=r['id'], kind='model_entries', count=p['entries']))
        for v in p['violations']:
            offenders.append(dict(item=r['id'], **v))
        if r['output'].get('calls') and not handlers:
            offenders.append(dict(item=r['id'], kind='no_call_handler_registered_on_model'))
    injected = sum(o.get('kind') == 'injected_token' for o in offenders)
    static = judge_static(findings, 'A2', dynamic)
    status = 'FAIL' if offenders or static else 'PASS'
    return clause(status, f'model entries per item {dict(entries)}; {injected} tokens fed that neither the model '
                          f'chose nor a registered handler emitted; {len(static)} static findings',
                  _compress(offenders)+[_finding(f) for f in static], handlers=handlers)


def _compress(offenders, keep=40):
    """Group identical violations by kind and innermost reader frame."""
    groups = defaultdict(list)
    for o in offenders:
        key = (o.get('kind'), (o.get('stack') or [''])[0])
        groups[key].append(o)
    out = []
    for (kind, frame), items in groups.items():
        first = dict(items[0])
        first['count'] = len(items)
        first['items'] = sorted({i.get('item') for i in items})[:10]
        out.append(first)
    return out[:keep]


def judge_static(findings, clause_id, dynamic):
    fails = [f for f in S.failing(findings, dynamic) if f['clause'] == clause_id]
    return fails


def judge_a3(findings, dynamic, scope_files):
    fails = judge_static(findings, 'A3', dynamic)
    by = Counter(f['rule'] for f in fails)
    return clause('FAIL' if fails else 'PASS', f'{len(fails)} findings in {len(scope_files)} call-path files '
                  f'{dict(by)}', [_finding(f) for f in fails], scope_files=sorted(scope_files))


def _finding(f):
    return dict(rule=f['rule'], file=f['file'], line=f['line'], function=f['function'], detail=f['detail'],
                text=f['text'])


def judge_a4(records, declared, findings, dynamic):
    names = {n for _, _, role, n in declared if role in MODEL_ROLES}
    offenders = []
    for r in records:
        out = r['output']
        gen = r['generated_text'] or ''
        if r['error']:
            offenders.append(dict(item=r['id'], kind='reader_error', detail=r['error']))
        answer = out.get('answer')
        if answer is None or str(answer).strip() == '' or str(answer).strip() not in gen:
            offenders.append(dict(item=r['id'], kind='answer_not_in_generated_sequence', answer=answer))
        if r['provenance'] and out.get('text') not in (None, gen) and out.get('text') != gen.rstrip():
            offenders.append(dict(item=r['id'], kind='reported_text_differs_from_generated_sequence'))
        for c in out.get('calls', []):
            fields = c.get('fields') or {}
            cited = {h for hs in fields.values() for h in (hs or [])}
            if not fields or not cited:
                offenders.append(dict(item=r['id'], kind='response_without_head', call=c.get('call'),
                                      response=str(c.get('response'))[:80]))
            elif cited-names:
                offenders.append(dict(item=r['id'], kind='response_cites_undeclared_module',
                                      modules=sorted(cited-names), call=c.get('call')))
    static = judge_static(findings, 'A4', dynamic)
    offenders = _compress(offenders)+[_finding(f) for f in static]
    return clause('FAIL' if offenders else 'PASS', f'{len(offenders)} offender groups '
                  f'({len(static)} static)', offenders)


def judge_a5(records, declared, findings, dynamic, sandbox=None, perturb=None, cache_proof=None):
    parts, offenders = {}, []
    # (iii) towers run inside the call
    towers = {n for _, _, role, n in declared if role == 'tower'}
    tower_off = []
    for r in records:
        cited = {h for c in r['output'].get('calls', []) for hs in (c.get('fields') or {}).values() for h in hs or []}
        runs = r['provenance']['module_runs'] if r['provenance'] else {}
        for t in sorted(cited & towers):
            if not runs.get(f'tower:{t}'):
                tower_off.append(dict(item=r['id'], kind='tower_cited_but_not_run_in_call', tower=t))
    static = judge_static(findings, 'A5', dynamic)
    proof = check_cache_proof(cache_proof) if cache_proof else None
    if proof is not None and proof['status'] != 'PASS':
        tower_off.append(dict(kind='cache_proof_invalid', detail=proof['reason']))
    parts['iii'] = 'FAIL' if tower_off or static else 'PASS'
    offenders += _compress(tower_off)+[_finding(f) for f in static]
    if sandbox is not None:
        parts['i'] = sandbox['status']
        offenders += sandbox.get('offenders', [])
    else:
        parts['i'] = 'NOT RUN'
    if perturb is not None:
        parts['ii'] = perturb['status']
        offenders += perturb.get('offenders', [])
    else:
        parts['ii'] = 'NOT RUN'
    status = 'FAIL' if 'FAIL' in parts.values() else 'PASS' if all(v == 'PASS' for v in parts.values()) else 'INCOMPLETE'
    return clause(status, f'parts {parts}', offenders, parts=parts, cache_proof=proof)


def check_cache_proof(path, minimum=50):
    try:
        data = json.loads(Path(path).read_text())
    except Exception as exc:
        return dict(status='FAIL', reason=f'unreadable proof: {exc}')
    items = data.get('items', [])
    if data.get('schema') != 'eat1-cache-proof-v1':
        return dict(status='FAIL', reason='schema differs')
    if len(items) < minimum:
        return dict(status='FAIL', reason=f'{len(items)} items < {minimum}')
    unequal = [i.get('id') for i in items if i.get('live') != i.get('cached')]
    if unequal:
        return dict(status='FAIL', reason=f'{len(unequal)} items differ', items=unequal[:10])
    return dict(status='PASS', reason=f'{len(items)} items equal', cache_sha256=data.get('cache_sha256'),
                note='a cache may speed a read; a claimed number still comes from a live run')


# ---------------------------------------------------------------- A5 (ii): head perturbation
def compare_calls(base, other):
    """Prefix-aligned comparison: a response is eligible while every earlier call and response match."""
    out = []
    for b, o in zip(base, other):
        if b.get('call') != o.get('call'):
            break
        cited = sorted({h for hs in (b.get('fields') or {}).values() for h in hs or []})
        changed = b.get('response') != o.get('response')
        out.append(dict(call=b.get('call'), cited=cited, changed=changed))
        if changed:
            break
    return out


def perturbation(reader, items, artifact, base_records, seeds=(1, 2, 3)):
    import torch
    declared = artifact.module_roles(reader.model)
    targets = [(p, m, r, n) for p, m, r, n in declared if r in ('head', 'tower')]
    report, offenders = {}, []
    base = {r['id']: r['output'].get('calls', []) for r in base_records}
    for path, mod, role, name in targets:
        saved = copy.deepcopy(mod.state_dict())
        verdicts = defaultdict(lambda: dict(changed=False, cited=None))
        try:
            for seed in seeds:
                g = torch.Generator().manual_seed(seed)
                with torch.no_grad():
                    for t in list(mod.parameters())+list(mod.buffers()):
                        if t.is_floating_point() and t.numel():
                            scale = float(t.detach().float().std()) if t.numel() > 1 else 0.
                            scale = scale if scale > 0 else float(t.detach().float().abs().mean())+1e-3
                            noise = torch.randn(t.shape, generator=g).to(t.device, t.dtype)
                            t.add_(noise*scale)
                runs, _, _ = observe(reader, items, artifact, trace_lines=False, audit=False, monitor=False)
                mod.load_state_dict(saved)
                for r in runs:
                    for k, c in enumerate(compare_calls(base.get(r['id'], []), r['output'].get('calls', []))):
                        v = verdicts[(r['id'], k)]
                        v['cited'] = name in c['cited']
                        v['call'] = c['call']
                        v['changed'] = v['changed'] or c['changed']
        finally:
            mod.load_state_dict(saved)
        naming = [(key, v) for key, v in verdicts.items() if v['cited']]
        others = [(key, v) for key, v in verdicts.items() if not v['cited']]
        unchanged_naming = [key for key, v in naming if not v['changed']]
        changed_others = [key for key, v in others if v['changed']]
        report[name] = dict(role=role, responses_naming=len(naming), naming_changed=len(naming)-len(unchanged_naming),
                            others=len(others), others_changed=len(changed_others))
        for key in unchanged_naming:
            offenders.append(dict(kind='response_names_module_but_did_not_change', module=name, item=key[0],
                                  call_index=key[1]))
        for key in changed_others:
            offenders.append(dict(kind='response_changed_by_module_it_does_not_name', module=name, item=key[0],
                                  call_index=key[1]))
    return dict(status='FAIL' if offenders else 'PASS', modules=report, offenders=_compress(offenders),
                seeds=list(seeds))


# ---------------------------------------------------------------- A5 (i): unmounted rerun
def sandbox_command(args, code_roots, binds_ro, out_dir):
    cmd = ['bwrap', '--die-with-parent', '--unshare-pid', '--proc', '/proc', '--dev-bind', '/dev', '/dev',
           '--tmpfs', '/tmp', '--setenv', 'HOME', '/tmp', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1']
    for p in ('/usr', '/etc', '/bin', '/sbin', '/lib', '/lib64', '/sys', '/opt'):
        if os.path.islink(p):
            cmd += ['--symlink', os.readlink(p), p]
        elif os.path.isdir(p):
            cmd += ['--ro-bind', p, p]
    env_paths = {sys.prefix, sys.base_prefix, str(Path(sys.executable).resolve().parent.parent)}
    for p in sorted(env_paths | set(code_roots) | set(binds_ro)):
        if p and os.path.exists(p):
            cmd += ['--ro-bind', p, p]
    cmd += ['--bind', str(out_dir), str(out_dir), '--chdir', '/tmp',
            '--setenv', 'PYTHONPATH', os.pathsep.join(sorted({str(EAT1_DIR.parent)} | set(args.pythonpath or [])))]
    cmd += [sys.executable, '-I' if False else '-B', '-m', 'eat1.run', '--child', '--reader', args.reader,
            '--reader-kwargs', args.reader_kwargs, '--items', str(Path(args.items).resolve()),
            '--out', str(out_dir)]
    if args.limit:
        cmd += ['--limit', str(args.limit)]
    return cmd


def run_sandbox(args, records, artifact, input_roots, out_dir):
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    code_roots = sorted({str(EAT1_DIR)} | set(args.code_root or []))
    binds = {str(artifact.root), str(artifact.path), str(Path(args.items).resolve())} | {
        str(Path(p).resolve()) for p in input_roots}
    cmd = sandbox_command(args, code_roots, binds, out_dir)
    (out_dir/'COMMAND.json').write_text(json.dumps(cmd, indent=1)+'\n')
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.sandbox_timeout)
    (out_dir/'child.log').write_text(proc.stdout[-20000:]+'\n---stderr---\n'+proc.stderr[-20000:])
    if proc.returncode != 0 or not (out_dir/'CHILD_OUTPUTS.json').is_file():
        return dict(status='FAIL', offenders=[dict(kind='sandboxed_run_failed', returncode=proc.returncode,
                                                   stderr_tail=proc.stderr[-600:])])
    child = {r['id']: r for r in json.loads((out_dir/'CHILD_OUTPUTS.json').read_text())}
    offenders = []
    for r in records:
        c = child.get(r['id'])
        if c is None or c['output'] != r['output'] or c['error'] != r['error']:
            offenders.append(dict(kind='output_differs_without_outside_directories', item=r['id'],
                                  child_error=None if c is None else c['error']))
    return dict(status='FAIL' if offenders else 'PASS', offenders=_compress(offenders),
                visible=code_roots+sorted(binds))


# ---------------------------------------------------------------- A6 report
def per_type(records):
    out = {}
    for typ in sorted({r['type'] for r in records}):
        rs = [r for r in records if r['type'] == typ]
        calls = [len(r['output'].get('calls', [])) for r in rs]
        fields = defaultdict(Counter)
        for r in rs:
            for c in r['output'].get('calls', []):
                for f, hs in (c.get('fields') or {}).items():
                    fields[f][','.join(hs or []) or 'none'] += 1
                if not c.get('fields'):
                    fields['(unattributed)']['none'] += 1
        secs = [r['seconds'] for r in rs]
        out[typ] = dict(items=len(rs), call_rate=sum(c > 0 for c in calls)/len(rs), calls_per_item=sum(calls)/len(rs),
                        heads_behind_fields={f: dict(c) for f, c in fields.items()},
                        seconds_mean=statistics.mean(secs), seconds_median=statistics.median(secs),
                        seconds_max=max(secs), errors=sum(bool(r['error']) for r in rs))
    return out


def write_report(out, result):
    out = Path(out)
    (out/'EAT1_REPORT.json').write_text(json.dumps(result, indent=1, default=str)+'\n')
    lines = [f'# EAT-1 report: {result["reader"]}', '',
             f'Artifact manifest {result["artifact"]} (sha256 {result["artifact_sha256"]}); items {result["items"]}; '
             f'mode {result["mode"]}; started {result["started_utc"]}.', '',
             '| Clause | Status | Summary |', '|---|---|---|']
    for k in ('A1', 'A2', 'A3', 'A4', 'A5'):
        c = result['clauses'][k]
        lines.append(f'| {k} | {c["status"]} | {c["summary"]} |')
    lines += ['', f'Overall: **{result["overall"]}**', '', '## Per type (A6)', '',
              '| Type | Items | Call rate | Calls/item | Heads behind response fields | s/item (mean, median, max) |',
              '|---|---|---|---|---|---|']
    for typ, v in result['per_type'].items():
        heads = '; '.join(f'{f}: {dict(c)}' for f, c in v['heads_behind_fields'].items()) or '-'
        lines.append(f'| {typ} | {v["items"]} | {v["call_rate"]:.3f} | {v["calls_per_item"]:.2f} | {heads} | '
                     f'{v["seconds_mean"]:.3f}, {v["seconds_median"]:.3f}, {v["seconds_max"]:.3f} |')
    lines += ['', '## Offenders by clause (file and line)', '']
    for k in ('A1', 'A2', 'A3', 'A4', 'A5'):
        c = result['clauses'][k]
        if not c['offenders']:
            continue
        lines += [f'### {k}', '']
        for o in c['offenders'][:60]:
            if 'rule' in o:
                lines.append(f'- `{o["rule"]}` {o["file"]}:{o["line"]} ({o["function"]}): {o["detail"]} — `{o["text"]}`')
            elif 'file' in o:
                lines.append(f'- outside data `{o["file"]}` (sha256 {o["sha256"][:12]}) opened at '
                             f'{(o.get("opened_at") or ["?"])[0]}')
            else:
                where = (o.get('stack') or [''])[0]
                lines.append(f'- {o.get("kind")} x{o.get("count", 1)} items {o.get("items", o.get("item"))} '
                             f'{where} {json.dumps({k2: v for k2, v in o.items() if k2 not in ("kind", "count", "items", "item", "stack")}, default=str)[:200]}')
        if len(c['offenders']) > 60:
            lines.append(f'- ... {len(c["offenders"])-60} more in EAT1_REPORT.json')
        lines.append('')
    (out/'EAT1_REPORT.md').write_text('\n'.join(lines)+'\n')


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--reader', required=True)
    ap.add_argument('--reader-kwargs', default='{}')
    ap.add_argument('--items', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--input-root', action='append', default=[])
    ap.add_argument('--code-root', action='append', default=[])
    ap.add_argument('--pythonpath', action='append', default=[])
    ap.add_argument('--allowlist')
    ap.add_argument('--allowlist-extra', action='append')
    ap.add_argument('--sandbox', action='store_true', help='A5 (i): rerun with outside directories unmounted')
    ap.add_argument('--sandbox-timeout', type=int, default=3600)
    ap.add_argument('--perturb', action='store_true', help='A5 (ii): perturb each head and tower')
    ap.add_argument('--strace-log')
    ap.add_argument('--no-verify-artifact', action='store_true')
    ap.add_argument('--child', action='store_true')
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    reader = load_reader(args.reader, json.loads(args.reader_kwargs))
    artifact = Artifact(reader.artifact_manifest, verify=not args.no_verify_artifact and not args.child)
    items = read_items(args.items, args.limit)
    if args.child:
        records, _, _ = observe(reader, items, artifact, trace_lines=False, audit=False, monitor=False)
        (out/'CHILD_OUTPUTS.json').write_text(json.dumps(
            [dict(id=r['id'], output=r['output'], error=r['error']) for r in records])+'\n')
        return 0
    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    input_roots = list(args.input_root)+[i['frames'] for i in items if isinstance(i.get('frames'), str)]
    records, lines, declared = observe(reader, items, artifact)
    strace = H.parse_strace(args.strace_log) if args.strace_log and Path(args.strace_log).is_file() else None
    a1 = judge_a1(records, artifact, input_roots, strace)
    scope = {f for f in lines if not H.is_harness(f)}
    allow = S.load_allowlist(args.allowlist, args.allowlist_extra)
    findings, suppressed = S.scan(sorted(scope), allow, executed={f: set(v) for f, v in lines.items()})
    sandbox = run_sandbox(args, records, artifact, input_roots, out/'a5_sandbox') if args.sandbox else None
    perturb = perturbation(reader, items, artifact, records) if args.perturb else None
    clauses = dict(A1=a1, A2=judge_a2(records, declared, findings, True), A3=judge_a3(findings, True, scope),
                   A4=judge_a4(records, declared, findings, True),
                   A5=judge_a5(records, declared, findings, True, sandbox, perturb,
                               getattr(reader, 'eat1_cache_proof', None)))
    overall = 'FAIL' if any(c['status'] == 'FAIL' for c in clauses.values()) else (
        'PASS' if all(c['status'] == 'PASS' for c in clauses.values()) else 'INCOMPLETE')
    result = dict(schema='eat1-report-v1', reader=args.reader, reader_kwargs=json.loads(args.reader_kwargs),
                  artifact=str(artifact.path), artifact_sha256=artifact.manifest_sha256, items=len(items),
                  mode='dynamic', started_utc=started, clauses=clauses, overall=overall,
                  per_type=per_type(records), suppressed=suppressed, perturbation=perturb,
                  declared_modules=[dict(path=p, role=r, name=n) for p, _, r, n in declared],
                  executed_scope={f: len(v) for f, v in lines.items()})
    (out/'ITEMS.jsonl').write_text(''.join(json.dumps(dict(id=r['id'], type=r['type'], seconds=r['seconds'],
        error=r['error'], output=r['output'], entries=r['provenance']['entries'],
        violations=len(r['provenance']['violations']), module_runs=r['provenance']['module_runs']),
        default=str)+'\n' for r in records))
    write_report(out, result)
    print(json.dumps(dict(overall=overall, **{k: c['status'] for k, c in clauses.items()})))
    return 0


if __name__ == '__main__':
    sys.exit(main())
