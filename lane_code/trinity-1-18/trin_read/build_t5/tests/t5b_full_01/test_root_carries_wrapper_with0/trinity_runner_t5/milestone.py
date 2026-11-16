"""D0 archive admission, sequential family reads, and measured proof cost projection."""
import argparse
from collections import Counter
import glob
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import time

import trinity_read as T
import compare_tokens as C

ITEMS_SHA = '2ab22b681533c48b7a8ba9a78b7d95d1ea78c4d76beb13ad2784d42738f2cbf1'
CHECKER = T.SJ/'orch_cd/legs1_reads/out/export_check.py'
CHECKER_PINS = {
    'export_check.py': '0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2',
    'common.py': '1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4',
}
PRIMARY_RULE = ('Main: released_answer on primary rows; tasks without primary rows use own answer. '
                'Away, forward (toward), camera: own answer. Item-weighted means; score_pct is 0–100.')


def inventory():
    path = Path(__file__).with_name('e193_items.json')
    if T.sha(path) != ITEMS_SHA: raise ValueError('e193 item inventory changed')
    return T.load(path)['families']


def validate_membership(family, ids, full=True):
    expected = inventory()[family]['items']
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(expected):
        raise ValueError('Selection differs from e193 membership')
    if full and set(ids) != set(expected): raise ValueError('Full family differs from e193 membership')


def validate_binding(family, cfg, tasks):
    ref = inventory()[family]
    if (cfg['cells'] != ref['cells'] or cfg['source_sha256'] != ref['source_sha256'] or
            cfg['datasets'][0]['rows']['sha256'] != ref['tasks_sha256']):
        raise ValueError('Family protocol or payload differs from e193')
    validate_membership(family, [t['example_id'] for t in tasks], full=True)
    if any(ref['items'][t['example_id']] != t['question_type'] for t in tasks):
        raise ValueError('Family task types differ from e193')


def completed_local(value, tar=False):
    path = Path(value).absolute()
    if '.part' in path.name or '.part' in path.resolve().name:
        raise ValueError('Never consume a .part file')
    if not T.inside(path.resolve(), Path('/scratch')) or path.resolve() != path or not path.is_file():
        raise ValueError('Require a completed regular local /scratch file without symlinks')
    if tar and path.suffix != '.tar': raise ValueError('Require a complete .tar file')
    return path


def run_export_checker(root, artifact, digest, step, full, receipt_dir, bwrap):
    config_path = root/'bootstrap/CONFIG.json'
    config = T.load(config_path)
    for name, pin in CHECKER_PINS.items():
        if T.sha(T.physical(root, CHECKER.parent/name)) != pin:
            raise ValueError('Export checker source changed: '+name)
    base = config['spec']['models']['base']['path']
    output = receipt_dir/'CHECK.json'
    argv = ['--export', artifact, '--sha256', digest, '--base', base,
            '--step', str(step), '--output', str(output)]
    if not full: argv.append('--header-only')
    env = T.environment(root)
    command = T.ns_command(root, config_path, CHECKER, argv, gpu=False, bwrap=bwrap, llguidance_stub=False)
    T.dump(receipt_dir/'COMMAND.json', dict(argv=command, gpu=False, source_sha256=CHECKER_PINS))
    with (receipt_dir/'check.log').open('xb') as log:
        result = subprocess.run(command, env=env, cwd=str(root), stdout=log, stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError('Export checker failed; inspect '+str(receipt_dir/'check.log'))
    checked = T.load(output)
    expected = 'VERIFIED' if full else 'HEADER_ONLY_NOT_VERIFIED'
    if checked.get('status') != expected or checked.get('step') != step:
        raise ValueError('Unexpected export checker result')
    return checked


def stage_export(args):
    root = T.writable(args.root)
    if args.run not in T.EXPORT_RUNS or type(args.step) is not int or args.step <= 0:
        raise ValueError('Require an allowed run and positive step')
    source = completed_local(args.tar, tar=True); done_path = completed_local(args.done)
    done = T.load(done_path)
    if (not isinstance(done, dict) or not isinstance(done.get('object'), str) or not done['object'].strip() or
            type(done.get('bytes')) is not int or done['bytes'] <= 0 or
            not isinstance(done.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', done['sha256'])):
        raise ValueError('Done record requires object, positive integer bytes, and whole-tar sha256')
    logical = str(T.FSW/'ap/8865619b/runs'/args.run/('m'+str(args.step))/'artifact.json')
    T.logical_artifact(root, logical, args.step)
    dest = T.physical(root, logical).parent
    if dest.resolve() != dest: raise ValueError('Export destination has a symlink')
    receipt_dir = root/'exports'/(args.run+'_m'+str(args.step))
    root.mkdir(parents=True, exist_ok=True)
    with T.lock(root/'.stage-export.lock'):
        if dest.exists() or receipt_dir.exists(): raise ValueError('Milestone or receipt exists; no overwrite or retry')
        # Hash and parse the same open file, never the arriving partial name.
        with source.open('rb') as stream:
            before = source.stat()
            if before.st_size != done['bytes']: raise ValueError('Tar bytes differ from done record')
            h = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
            if h.hexdigest() != done['sha256']: raise ValueError('Tar SHA256 differs from done record')
            stream.seek(0)
            with tarfile.open(fileobj=stream, mode='r:') as archive:
                members = []; names = set(); sizes = 0
                for member in archive:
                    path = PurePosixPath(member.name)
                    if (path.is_absolute() or '..' in path.parts or not path.parts or
                            path.parts[0] != dest.name or not (member.isfile() or member.isdir())):
                        raise ValueError('Unsafe member or unexpected milestone layout: '+member.name)
                    name = str(path)
                    if name in names: raise ValueError('Duplicate tar member: '+name)
                    names.add(name)
                    rel = path.parts[1:]
                    if rel and (rel[0] not in ('artifact.json', 'heads.pt', 'full_weights') or
                                (rel[0] != 'full_weights' and (len(rel) != 1 or not member.isfile()))):
                        raise ValueError('Unexpected milestone layout: '+name)
                    if not rel and not member.isdir(): raise ValueError('Milestone root must be a directory')
                    if rel == ('full_weights',) and not member.isdir(): raise ValueError('Weights must be a directory')
                    members.append((member, path))
                    if member.isfile(): sizes += member.size
                files = {str(p) for m, p in members if m.isfile()}
                required = {dest.name+'/'+p for p in ('artifact.json', 'heads.pt', 'full_weights/full_weights.json')}
                if not required <= files: raise ValueError('Missing required milestone layout')
                for name in names:
                    if any(str(p) in files for p in PurePosixPath(name).parents):
                        raise ValueError('File/directory collision in tar')
                T.kit_stage().room(root, sizes)
                receipt_dir.mkdir(parents=True)
                receipt = dict(schema=1, status='extracting', run=args.run, step=args.step,
                    source=str(source), done_path=str(done_path), done_sha256=T.sha(done_path), done=done,
                    tar_bytes=before.st_size, tar_sha256=h.hexdigest(), extracted_bytes=sizes,
                    artifact=logical, checker_mode='full' if args.full else 'header-only',
                    members=len(members), started=time.time())
                T.dump(receipt_dir/'RECEIPT.json', receipt)
                try:
                    dest.mkdir(parents=True)
                    for member, path in members:
                        target = dest.parent/str(path)
                        if member.isdir(): target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with archive.extractfile(member) as inp, target.open('xb') as out:
                                shutil.copyfileobj(inp, out, 1024*1024)
                            target.chmod(0o600)
                    after = source.stat()
                    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                        raise ValueError('Tar changed during staging')
                    receipt['status'] = 'extracted'
                    receipt['artifact_sha256'] = T.sha(dest/'artifact.json')
                    T.dump(receipt_dir/'RECEIPT.json', receipt)
                    receipt['checker'] = run_export_checker(root, logical, receipt['artifact_sha256'], args.step,
                                                           args.full, receipt_dir, args.bwrap)
                    receipt['status'] = 'complete'
                    return receipt
                except Exception as error:
                    receipt.update(status='failed', error=str(error))
                    raise
                finally:
                    receipt['finished'] = time.time()
                    T.dump(receipt_dir/'RECEIPT.json', receipt)


def parse_families(value=None):
    families = list(T.FAMILIES) if value is None else value.split(',')
    if not families or len(set(families)) != len(families) or any(f not in T.FAMILIES for f in families):
        raise ValueError('Require unique comma-separated families: '+','.join(T.FAMILIES))
    return families


def aggregate(rows, field):
    values = [r['scores'][field] for r in rows if r['scores'].get(field) is not None]
    if any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise ValueError('Invalid primary score')
    return dict(items=len(rows), scored=len(values), score_pct=100*sum(values)/len(values) if values else None)


def primary_scores(report, family):
    rows = report['rows']
    primary = [r for r in rows if r['stratum'] == 'primary'] if family == 'main' else []
    field = 'released_answer' if primary else 'answer'
    selected = primary if primary else rows
    tasks = {}
    for task in sorted({r['question_type'] for r in rows}):
        group = [r for r in rows if r['question_type'] == task]
        chosen = [r for r in group if r['stratum'] == 'primary'] if family == 'main' else []
        basis = 'released_answer' if chosen else 'answer'
        tasks[task] = dict(aggregate(chosen or group, basis), scoring_basis=basis,
                           selection='primary' if chosen else 'all', total_items=len(group))
    return dict(overall=dict(aggregate(selected, field), scoring_basis=field,
                            selection='primary' if primary else 'all'), per_task=tasks,
                all_own_gt=aggregate(rows, 'answer'), total_items=len(rows))


def family_summary(packet, family, attempt):
    done = T.load(packet/'COMPLETE.json')
    validate_membership(family, done['ids'])
    exit_info = T.load(packet/'EXIT.json')
    if exit_info['returncode'] != 0 or exit_info.get('yielded') or exit_info.get('sampler_errors'):
        raise ValueError('Family execution failed')
    report = T.load(packet/'report/B2048.json')
    if report.get('arm') != 'B2048': raise ValueError('Wrong summary arm')
    rows = report['rows']; expected = inventory()[family]['items']
    keys = [r['key'].split(':', 1)[1] for r in rows]
    validate_membership(family, keys)
    if any(expected[k] != r['question_type'] for k, r in zip(keys, rows)):
        raise ValueError('Summary task membership differs')
    result = primary_scores(report, family)
    result.update(status='complete', label='toward' if family == 'forward' else family,
                  packet=str(packet), wall_seconds=exit_info['wall_seconds'], card=T.load(packet/'CARD.json'),
                  report_sha256=T.sha(packet/'report/B2048.json'))
    result['timing'] = {arm:C.timing(packet/'direct'/family, arm, done['ids']) for arm in C.ARMS}
    # Keep item latency in the journals, expose compact measured timing here.
    for measured in result['timing'].values(): measured.pop('items')
    return result


def write_summary(out, value):
    T.dump(out/'MILESTONE_SUMMARY.json', value)
    lines = ['Milestone read status: '+value['status']+'.', '', PRIMARY_RULE, '',
             'Card: '+str(value['gpu'])+'. Total wall seconds: '+str(value['wall_seconds'])+'.', '',
             '| Family | Status | Items | Primary B2048 % | Family wall seconds |',
             '|---|---|---:|---:|---:|']
    for family, row in value['families'].items():
        lines.append('| {} | {} | {} | {} | {} |'.format(row.get('label', family), row['status'],
            row.get('total_items'), row.get('overall', {}).get('score_pct'), row.get('invocation_wall_seconds')))
    lines += ['', '| Family | Task | Items scored / total | B2048 % | Label basis |', '|---|---|---:|---:|---|']
    for family, row in value['families'].items():
        for task, score in row.get('per_task', {}).items():
            lines.append('| {} | {} | {} / {} | {} | {} ({}) |'.format(row.get('label', family), task,
                score['scored'], score['total_items'], score['score_pct'], score['scoring_basis'], score['selection']))
        for arm, timing in row.get('timing', {}).items():
            lines += ['', '{} {}: {} generated tokens per summed request-latency second ({} measured items).'.format(
                family, arm, timing['generated_tokens_per_sum_latency'], timing['measured_items'])]
    if value.get('error'): lines += ['', 'Failure: '+value['error']]
    lines += ['', 'Request-latency token rates are not card wall-clock throughput. Missing measurements remain null.', '']
    (out/'MILESTONE_SUMMARY.md').write_text('\n'.join(lines))


def read_families(args):
    families = parse_families(None if args.all_families else args.families)
    if args.ids or args.first is not None: raise ValueError('Multi-family read requires full families')
    if args.model_slot and any(f not in ('main', 'camera') for f in families):
        raise ValueError('Model slots support only main and camera')
    root = T.writable(args.root); out = T.writable(args.out)
    if not T.inside(out, root): raise ValueError('Runtime output must be under --root')
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', args.token): raise ValueError('Invalid milestone token')
    if out.exists(): raise ValueError('Milestone output exists; no retry')
    pattern = T.yield_pattern(args.yield_glob)
    tokens = root/'tokens'; tokens.mkdir(parents=True, exist_ok=True)
    with (tokens/args.token).open('x') as stream: stream.write(str(out)+'\n')
    out.mkdir(parents=True)
    started = time.monotonic()
    value = dict(schema=1, reference='e193c2a3c', status='running', gpu=str(args.gpu),
                 artifact=args.artifact, artifact_sha256=args.sha256, step=args.step,
                 primary_rule=PRIMARY_RULE, wall_seconds=0, families={f:dict(status='pending') for f in families})
    active = None
    try:
        for family in families:
            active = family
            matched = sorted(p for p in glob.glob(pattern) if Path(p).is_file()) if pattern else []
            if matched:
                T.dump(out/'YIELD.json', dict(matched_file=matched[0], time=time.time(), between_families=True, next_family=family))
                value['status'] = 'yielded'
                raise RuntimeError('Yield requested before '+family+'; no retry')
            child = argparse.Namespace(**vars(args)); child.families = None; child.all_families = False
            child.family = family; child.out = str(out/family)
            # A deterministic fresh token per family satisfies the original token syntax.
            child.token = 'd'+hashlib.sha256((args.token+':'+family).encode()).hexdigest()[:24]
            before = time.monotonic()
            try:
                T.launch(child)
                value['families'][family] = family_summary(out/family, family, child.token)
            except Exception as error:
                value['families'][family].update(status='failed', error=str(error), packet=str(out/family))
                if (out/family/'YIELD.json').exists(): value['status'] = 'yielded'
                raise
            finally:
                value['families'][family]['invocation_wall_seconds'] = time.monotonic()-before
                value['wall_seconds'] = time.monotonic()-started
                write_summary(out, value)
        value['status'] = 'complete'
    except Exception as error:
        if value['status'] != 'yielded': value['status'] = 'failed'
        value.update(error=str(error), stopped_at=active)
        raise
    finally:
        value['wall_seconds'] = time.monotonic()-started
        write_summary(out, value)
    return value


def cost(proof):
    proof = T.writable(proof)
    exit_info = T.load(proof/'EXIT.json')
    wall = exit_info.get('wall_seconds')
    if (exit_info.get('returncode') != 0 or exit_info.get('yielded') or exit_info.get('sampler_errors') or
            type(wall) not in (int, float) or not math.isfinite(wall) or wall <= 0):
        raise ValueError('Cost requires a completed proof with positive EXIT wall time')
    dest = proof/'b0/d0'; ids = None; arms = {}
    for arm, rel in C.ARMS.items():
        records = C.unique(C.rows(dest/'results'/rel/'items_b0.jsonl'))
        if not records or any(r.get('status') != 'complete' for r in records.values()):
            raise ValueError('Cost requires completed items in every proof arm')
        if ids is None: ids = sorted(records)
        elif set(ids) != set(records): raise ValueError('Proof arm membership differs')
        measured = C.timing(dest, arm, ids)
        items = measured['items']
        if any(r['seconds'] is None and not r['reused_on_generation'] for r in items):
            raise ValueError('Missing generation latency or budget receipt for '+arm)
        seconds = sum(r['seconds'] or 0 for r in items)
        arms[arm] = dict(sum_request_seconds=seconds, seconds_per_item=seconds/len(ids),
                         generated_items=sum(r['seconds'] is not None for r in items),
                         reused_items=sum(r['reused_on_generation'] for r in items),
                         tokens_per_sum_latency=measured['generated_tokens_per_sum_latency'])
    total_latency = sum(a['sum_request_seconds'] for a in arms.values())
    if total_latency <= 0: raise ValueError('No measured proof generation')
    families = {f:dict(items=len(r['items']), per_task=dict(Counter(r['items'].values()))) for f, r in inventory().items()}
    for row in families.values(): row['projected_wall_minutes'] = wall/len(ids)*row['items']/60
    for row in arms.values():
        row['allocated_wall_seconds_per_item'] = wall/len(ids)*row['sum_request_seconds']/total_latency
    value = dict(schema=1, proof=str(proof), reference='e193c2a3c', proof_items=len(ids),
                 proof_wall_seconds=wall, wall_seconds_per_item=wall/len(ids), arms=arms, families=families,
                 milestone_items=sum(r['items'] for r in families.values()),
                 projected_wall_minutes=sum(r['projected_wall_minutes'] for r in families.values()),
                 card=T.load(proof/'CARD.json') if (proof/'CARD.json').exists() else None,
                 model='Linear EXIT wall_seconds / proof items × full e193 counts on one card.',
                 limitations='Assumes the proof mix, concurrency and setup cost per item transfer to all families. '
                             'Arm seconds/item sum concurrent request latency; allocated arm wall times are estimates, not measured arm wall times. '
                             'Includes proof setup in EXIT; excludes outer preflight, transfer and stage-export. No reuse latency is counted twice.')
    T.dump(proof/'COST.json', value)
    return value
