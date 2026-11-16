#!/usr/bin/env python3
"""Trinity boundary for the reviewed ReVSI reader and receipt-gated D0 overlay. No remote operations."""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
sys.dont_write_bytecode = True
import trinity_read as T
import rv_d0 as D

BUILD = Path(__file__).resolve().parent
KIT = BUILD/'rv_payload'
LOGICAL_KIT = '/scratch/jjyeung/rvkit'
LOGICAL_MEDIA = '/scratch/jjyeung/rvmedia'
ARMS = {'ON16k': 'items_a0.jsonl', 'B2048': 'budget_2048.jsonl', 'B4096': 'budget_4096.jsonl'}
GROUPS = {
    'object_counting': ('object_counting_single', 'object_counting_multiple'),
    'object_rel_direction': ('object_rel_direction_forward_easy', 'object_rel_direction_backward_easy',
                             'object_rel_direction_forward_hard', 'object_rel_direction_backward_hard'),
    'object_rel_distance': ('object_rel_distance_closest', 'object_rel_distance_farthest'),
    'object_size_estimation': ('object_size_estimation',), 'route_planning': ('route_planning',)}


def local(path):
    path = Path(path).absolute()
    if not T.inside(path.resolve(), T.AREA):
        raise ValueError('Runtime paths must remain under '+str(T.AREA))
    return path.resolve()


def pins_check():
    pins = T.load(BUILD/'RV_PAYLOAD_PINS.json')
    for name, pin in pins.items():
        p = KIT/name
        if p.is_symlink() or p.stat().st_size != pin['bytes'] or T.sha(p) != pin['sha256']:
            raise ValueError('Reviewed kit pin differs: '+name)
    # Include the exact production interpreter wrapper and transport descriptor.
    extras = {str(p.relative_to(KIT)) for p in KIT.rglob('*') if p.is_file()} - set(pins)
    if extras or any(p.is_symlink() for p in KIT.rglob('*')):
        raise ValueError('Unpinned kit files: '+str(extras))
    wrapper = '#!/bin/sh\nexec '+str(T.VLLM_ENV/'bin/python')+' -I "$@"\n'
    if (KIT/'vllm_isolated.sh').read_text() != wrapper:
        raise ValueError('Interpreter wrapper differs')
    return T.sha(BUILD/'RV_PAYLOAD_PINS.json')


def need_rows(path):
    rows = T.load(path); result = {}
    for row in rows:
        name = row['relative_path']; p = PurePosixPath(name)
        if p.is_absolute() or str(p) != name or '..' in p.parts or not name.endswith('.mp4'):
            raise ValueError('Unsafe media name')
        if name in result or type(row['bytes']) is not int or row['bytes'] <= 0 or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Invalid media manifest')
        result[name] = {k: row[k] for k in ('bytes', 'sha256')}
    if not result: raise ValueError('Empty media manifest')
    return result


def extract_media(archive, destination, need):
    """Never extract tar metadata or links; retain partial evidence on any failure."""
    archive = Path(archive); destination = Path(destination)
    if archive.is_symlink() or not archive.is_file() or archive.name.endswith('.part'):
        raise ValueError('Require a complete regular media archive')
    expected = need_rows(need)
    if os.path.lexists(str(destination)) or destination.resolve() != destination.absolute():
        raise ValueError('Media destination exists or has a symlink ancestor')
    # Check every header before creating any destination.
    with tarfile.open(str(archive), 'r:') as tf:
        seen = set()
        for member in tf:
            name = member.name
            if name in seen or name not in expected or not member.isreg() or member.issparse() or member.size != expected[name]['bytes']:
                raise ValueError('Unexpected, duplicate, unsafe, or wrong-size tar member: '+name)
            seen.add(name)
        if seen != set(expected): raise ValueError('Media inventory differs')
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(str(archive), 'r:') as tf:
        seen = set()
        for member in tf:
            if member.name in seen or member.name not in expected or not member.isreg() or member.issparse() or member.size != expected[member.name]['bytes']:
                raise ValueError('Archive changed during staging')
            seen.add(member.name)
            target = destination/member.name; target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(); size = 0
            with tf.extractfile(member) as src, target.open('xb') as dst:
                for chunk in iter(lambda: src.read(1024*1024), b''):
                    digest.update(chunk); size += len(chunk); dst.write(chunk)
            if size != expected[member.name]['bytes'] or digest.hexdigest() != expected[member.name]['sha256']:
                raise ValueError('Media SHA256 differs: '+member.name+'; partial destination retained')
        if seen != set(expected): raise ValueError('Archive inventory changed during staging')
    receipt = dict(schema='revsi-media-v1', complete=True, archive=str(archive.resolve()),
                   archive_sha256=T.sha(archive), archive_bytes=archive.stat().st_size,
                   need_sha256=T.sha(need), files=expected, namespace_target=LOGICAL_MEDIA)
    T.dump(destination/'RECEIPT.json', receipt)
    return receipt


def media_check(root):
    directory = root/'rv_media'; expected = need_rows(KIT/'media/NEED_261.json')
    receipt = T.load(directory/'RECEIPT.json')
    if not receipt.get('complete') or receipt['files'] != expected or receipt['need_sha256'] != T.sha(KIT/'media/NEED_261.json'):
        raise ValueError('Media receipt differs')
    for name, pin in expected.items():
        p = directory/name
        if p.is_symlink() or p.resolve() != p or p.stat().st_size != pin['bytes'] or T.sha(p) != pin['sha256']:
            raise ValueError('Staged media differs: '+name)
    return receipt


def runtime_check(root):
    wanted = T.load(KIT/'launcher/ORCHARD_ASSETS.json')
    staged = T.load(root/'bootstrap/CONFIG.json')['assets']
    differences = [key for key in sorted(set(wanted)|set(staged)) if wanted.get(key) != staged.get(key)]
    state = T.load(root/'STAGING.json')
    for name in ('runtime_0', 'runtime_1', 'runtime_2', 'base', 'export'):
        if state['pieces'].get(name, {}).get('status') != 'complete': differences.append(name+' incomplete')
    if differences: raise ValueError('Runtime pins differ; stop without substitutes: '+', '.join(differences))
    return dict(assets_identical=True, differences=[], vllm='0.32.0',
                assets_sha256=T.sha(KIT/'launcher/ORCHARD_ASSETS.json'))


def select_artifact(root, path, digest, frames=32):
    if frames != 32:
        raise ValueError('64 frames unavailable: kit pins tier 32, 32 anchors, frame plan and prompt pins; new media and reviewed pins required')
    path = D.regular(path)
    path = local(path)
    artifact = T.load(path); step = artifact.get('step')
    if type(step) is not int or step <= 0: raise ValueError('Invalid artifact step')
    logical = T.logical_artifact(root, str(path), step)
    if T.sha(path) != digest: raise ValueError('Artifact SHA256 differs')
    expected = T.load(KIT/'launcher/MODELS.json')['cp1m200']
    if step == 544 and logical == expected['path'] and digest == expected['sha256']:
        return dict(expected)
    selected = dict(kind='c1_export', path=logical, sha256=digest)
    D.admit(root, selected)
    return selected


def namespace(root, gpu=False, shm=None, bwrap=T.DEFAULT_BWRAP, llguidance_stub=True, adapter=None, packet=None):
    argv = T.namespace(root, gpu=gpu, shm=shm, bwrap=bwrap, llguidance_stub=llguidance_stub)
    # The inherited namespace expects an installed wrapper. Bind this build directly instead.
    pos = argv.index(str(root/'trinity_runner_t6')); argv[pos] = str(BUILD)
    argv += ['--ro-bind', str(BUILD), '/trinity-rv', '--ro-bind', str(KIT), LOGICAL_KIT]
    if (root/'rv_media').is_dir(): argv += ['--ro-bind', str(root/'rv_media'), LOGICAL_MEDIA]
    if adapter is not None:
        D.verify_overlay(packet, KIT, adapter)
        argv += ['--ro-bind', str(packet/D.OVERLAY), D.TARGET]
    return argv


def card_admission(index, output, pause=time.sleep):
    evidence = dict(rule='two empty readings, 60 seconds apart; same UUID; >=40 GiB and <100 MiB; no compute processes', readings=[], passed=False)
    try:
        evidence['readings'].append(dict(T.check_card(index), utc=time.time()))
        T.dump(output, evidence)
        pause(60)
        evidence['readings'].append(dict(T.check_card(index), utc=time.time()))
        if evidence['readings'][0]['uuid'] != evidence['readings'][1]['uuid']:
            raise ValueError('Card UUID changed')
        evidence['passed'] = True
    except Exception as error:
        evidence['error'] = str(error)
        raise
    finally: T.dump(output, evidence)
    return evidence


def make_config(root, out, mode, artifact, adapter=None):
    models = T.load(KIT/'launcher/MODELS.json'); models['cp1m200'] = artifact
    spec = dict(schema='a1', step=544, scope='direct', artifact=artifact, models=models,
                run=str(out), package=LOGICAL_KIT,
                interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python', vllm=LOGICAL_KIT+'/vllm_isolated.sh'),
                inputs=dict(rows=LOGICAL_KIT+'/inputs/i1.json', video_root=LOGICAL_MEDIA,
                            frame_plan=LOGICAL_KIT+'/cohort/FRAME_PLAN.json'))
    if adapter is not None:
        spec['step'] = adapter['step']
        spec['adapter_overlay'] = adapter
    # The kit computes its frame plan from all 261 authenticated clips.
    spec['inputs']['frame_plan'] = str(out/'SUPPLIED_FRAME_PLAN_NOT_PRESENT.json')
    return dict(spec=spec, mode=mode, phase_b=False, output=str(out),
                plan_sha256=hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                release=dict(transport=dict(path=LOGICAL_KIT+'/TRANSPORT.json', sha256=T.sha(KIT/'TRANSPORT.json'))))


def proof_check(path, root, artifact, kit_pin):
    path = local(path); done = T.load(path/'EXIT.json'); proof = T.load(path/'PARITY.json')
    spec = T.load(path/'CONFIG.json')
    if done.get('status') != 'COMPLETE' or done.get('kit_pin') != kit_pin or spec['mode'] != 'proof' or spec['spec']['artifact'] != artifact:
        raise ValueError('Require a completed rv-proof for this kit and artifact')
    if proof.get('items') != 20 or not all(proof.get(k) is True for k in ('processor_checked','all_prompt_bytes_equal','prompt_pins_equal')):
        raise ValueError('20-item processor proof incomplete')
    verify_outputs(path, done)
    if artifact != T.load(KIT/'launcher/MODELS.json')['cp1m200']:
        adapter = spec['spec'].get('adapter_overlay')
        current = D.admit(root, artifact)
        if not adapter or any(adapter.get(k) != v for k, v in current.items()):
            raise ValueError('D0 proof admission differs')
        D.verify_overlay(path, KIT, adapter)
        D.audit_bound(path, adapter)
        if T.load(path/D.RECEIPT) != adapter or T.load(path/'PROOF_SCOPE.json') != D.proof_scope(current):
            raise ValueError('D0 proof overlay or scope differs')
    return dict(path=str(path), exit_sha256=T.sha(path/'EXIT.json'), parity_sha256=T.sha(path/'PARITY.json'))


def output_pins(out):
    names = ['CONFIG.json', 'COMPLETE.json', 'SANDBOX.json', 'CARD.json', 'LLGUIDANCE.json']
    names += ['report/'+arm+'.json' for arm in ARMS]
    names += ['a0/results/0/'+name for name in ARMS.values()]
    if (out/'PARITY.json').exists(): names.append('PARITY.json')
    if T.load(out/'CONFIG.json')['spec'].get('adapter_overlay') is not None:
        names += [D.RECEIPT, D.OVERLAY, 'PROOF_SCOPE.json', 'ADMISSION.json', 'a0/request.json', 'a0/CODE_PINS.json']
    return {name: T.sha(out/name) for name in names}


def verify_outputs(out, done):
    pins = done.get('output_pins')
    if not pins or pins != output_pins(out): raise ValueError('Completed packet output pins differ')


def launch(args):
    root = local(args.root); out = local(args.out)
    if not T.inside(out, root) or out == root: raise ValueError('Packet must be under --root')
    if os.path.lexists(str(out)): raise ValueError('Packet exists; never resume or retry automatically')
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', args.token): raise ValueError('Invalid token')
    # All unsupported paths fail before GPU admission or model execution.
    artifact = select_artifact(root, args.artifact, args.sha256, args.frames)
    identity = None if artifact == T.load(KIT/'launcher/MODELS.json')['cp1m200'] else D.admit(root, artifact)
    kit_pin = pins_check(); runtime = runtime_check(root); media = media_check(root)
    mode = 'proof' if args.command == 'rv-proof' else 'production'
    proof = proof_check(args.proof, root, artifact, kit_pin) if mode == 'production' else None
    reserve = 200*1024**3 + 45*1024**3
    if shutil.disk_usage(root).free < reserve: raise ValueError('Require 200 GiB floor plus 45 GiB model/frame/output reserve')
    tokens = root/'rv_tokens'; tokens.mkdir(exist_ok=True)
    with (tokens/args.token).open('x') as stream: stream.write(str(out)+'\n')
    out.mkdir(parents=True, exist_ok=False)
    code = None; sampler = None; started = time.monotonic(); error = None
    log_path = out/'llg_stub_calls.jsonl'; log_path.touch(exist_ok=False)
    try:
        adapter = D.write_overlay(out, KIT, identity) if identity else None
        if adapter:
            T.dump(out/'PROOF_SCOPE.json', D.proof_scope(identity))
        config = make_config(root, out, mode, artifact, adapter)
        T.dump(out/'CONFIG.json', config)
        T.dump(out/'ADMISSION.json', dict(runtime=runtime, media_receipt_sha256=T.sha(root/'rv_media/RECEIPT.json'),
                                         kit_pin=kit_pin, proof=proof, free_bytes=shutil.disk_usage(root).free, reserve_bytes=reserve))
        env = T.environment(root, str(args.gpu), args.token)
        env['LLG_STUB_LOG'] = str(log_path)
        executed = T.bwrap_evidence(root, args.bwrap); overlay = T.llguidance_evidence(True)
        ns = namespace
        if adapter is not None:
            def ns(*pos, **kw):
                return namespace(*pos, adapter=adapter, packet=out, **kw)
        probe = None
        try:
            probe = T.probe(root, bwrap=args.bwrap, namespace_factory=ns)
        except Exception as exc:
            probe = getattr(exc, 'probe_report', dict(passed=False, error=str(exc)))
            raise
        finally:
            T.dump(out/'PROBE.json', probe)
            T.dump(out/'SANDBOX.json', T.sandbox_receipt(None, executed, overlay, probe))
        if probe['versions'].get('vllm') != '0.32.0': raise ValueError('Runtime vLLM differs; stop')
        command = ns(root, gpu=True, bwrap=executed['path']) + [str(T.VLLM_ENV/'bin/python'), '-I', '-B',
                    '/trinity-rv/rv_entry.py', str(root), str(out/'CONFIG.json')]
        receipt = T.sandbox_receipt(command, executed, overlay, probe)
        if adapter is not None: receipt['adapter_overlay'] = adapter
        T.dump(out/'SANDBOX.json', receipt)
        card_admission(str(args.gpu), out/'CARD.json')
        if adapter is not None: D.verify_overlay(out, KIT, adapter)
        argv = [T.VNICE, ' '.join(shlex.quote(s) for s in command)]
        T.dump(out/'COMMAND.json', dict(argv=argv, kit_pin=kit_pin, llguidance_stub=overlay))
        T.dump(out/'ENV.json', env)
        sampler = T.Sampler(str(args.gpu), out/'MEMORY.jsonl'); sampler.thread.start()
        receipt['namespace_executed'] = True; T.dump(out/'SANDBOX.json', receipt)
        with (out/'run.log').open('xb') as log:
            code = subprocess.call(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
        if code: raise RuntimeError('Kit exited '+str(code)+'; no automatic retry')
        if adapter is not None:
            D.verify_overlay(out, KIT, adapter)
            D.audit_bound(out, adapter)
        complete = T.load(out/'COMPLETE.json')
        if complete['items'] != (10 if mode == 'proof' else 679) or complete['mode'] != mode:
            raise ValueError('Kit completion membership differs')
        for arm in ARMS:
            report = T.load(out/'report'/(arm+'.json'))
            if report['items'] != complete['items'] or set(report['groups']) != set(GROUPS):
                raise ValueError('Kit report membership differs')
        if mode == 'proof':
            p = T.load(out/'PARITY.json')
            if p.get('items') != 20 or not all(p.get(k) is True for k in ('processor_checked','all_prompt_bytes_equal','prompt_pins_equal')):
                raise ValueError('Kit processor parity failed')
    except BaseException as exc:
        error = type(exc).__name__+': '+str(exc)
        raise
    finally:
        if sampler:
            sampler.stop.set(); sampler.thread.join(timeout=35)
        usage = T.stub_usage(log_path)
        sampler_errors = sampler.errors if sampler else []
        passed = code == 0 and error is None and usage['passed'] and not sampler_errors
        T.dump(out/'LLGUIDANCE.json', usage)
        outputs = None
        if passed:
            try: outputs = output_pins(out)
            except Exception as exc:
                passed = False; error = 'Incomplete packet: '+str(exc)
        T.dump(out/'EXIT.json', dict(status='COMPLETE' if passed else 'FAILED', returncode=code, error=error,
            wall_seconds=time.monotonic()-started, stub_usage=usage, sampler_errors=sampler_errors, kit_pin=kit_pin,
            output_pins=outputs,
            complete_requires='EXIT.status COMPLETE and kit COMPLETE.json'))
    if not passed: raise RuntimeError('Run audit failed; inspect EXIT.json; no automatic retry')
    return dict(output=str(out), status='COMPLETE', generation_synthetic=mode == 'proof')


def packet(path):
    p = Path(path).resolve()
    if (p/'packet/COMPLETE.json').is_file(): p = p/'packet'
    c = T.load(p/'COMPLETE.json')
    if c.get('mode') != 'production' or c.get('items') != 679 or c.get('generation_synthetic') is not False:
        raise ValueError('Comparison requires completed nonsynthetic 679-item production packets')
    exit_path = p/'EXIT.json' if (p/'EXIT.json').exists() else p.parent/'fetched/EXIT.json'
    done = T.load(exit_path)
    if done.get('status') != 'COMPLETE': raise ValueError('Packet exit is not COMPLETE')
    if 'kit_pin' in done: verify_outputs(p, done)
    spec = T.load(p/'SPEC.json')
    if spec.get('step') != 544 or spec.get('artifact', {}).get('sha256') != T.load(KIT/'launcher/MODELS.json')['cp1m200']['sha256']:
        raise ValueError('Parity comparison requires step-544 artifacts')
    return p


def indexed(rows):
    result = {}
    for row in rows:
        key = str(row.get('example_id', row.get('id')))
        if key in result or key == 'None': raise ValueError('Duplicate or missing item ID')
        result[key] = row
    return result


def journal(path):
    with Path(path).open() as stream: return indexed(json.loads(line) for line in stream if line.strip())


def divergence(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: return dict(index=i, a=x, b=y)
    if len(a) != len(b):
        i = min(len(a), len(b)); return dict(index=i, a=a[i] if i<len(a) else None, b=b[i] if i<len(b) else None)
    return None


def compare(a, b):
    a, b = packet(a), packet(b)
    cohort = journal(KIT/'cohort/c5.jsonl')
    result = dict(a=str(a), b=str(b), primary='B2048', arms={})
    for arm, filename in ARMS.items():
        left, right = journal(a/'a0/results/0'/filename), journal(b/'a0/results/0'/filename)
        reports = [T.load(p/'report'/(arm+'.json')) for p in (a, b)]
        if set(left) != set(cohort) or set(right) != set(cohort): raise ValueError('Comparison membership differs')
        details = []
        for key in sorted(cohort):
            x, y = left[key], right[key]
            for r in (x, y):
                ids = r.get('token_ids')
                if not isinstance(ids, list) or any(type(v) is not int or v<0 for v in ids): raise ValueError('Missing or malformed token IDs')
                if r['question_type'] != cohort[key]['question_type']: raise ValueError('Question type differs')
            first = divergence(x['token_ids'], y['token_ids'])
            details.append(dict(id=key, question_type=x['question_type'], tokens_equal=first is None,
                first_divergence=first, tokens_a=len(x['token_ids']), tokens_b=len(y['token_ids']),
                raw_generation_equal=x.get('raw_generation') == y.get('raw_generation')))
        groups = {}
        report_rows = [indexed(r['rows']) for r in reports]
        for rows, raw in zip(report_rows, (left, right)):
            if set(rows) != set(cohort): raise ValueError('Report membership differs')
            for k in cohort:
                expected = 0.0 if raw[k].get('status') != 'complete' or raw[k].get('derivation_error') else raw[k]['score']
                if rows[k]['score'] != expected: raise ValueError('Scorer row differs from journal score')
        for name, types in GROUPS.items():
            ids = [k for k in cohort if cohort[k]['question_type'] in types]
            scores = [[rs[k]['score'] for k in ids] for rs in report_rows]
            for rs in report_rows:
                for k in ids:
                    if rs[k]['question_type'] != cohort[k]['question_type'] or type(rs[k]['score']) not in (float,int) or not math.isfinite(rs[k]['score']) or not 0 <= rs[k]['score'] <= 1:
                        raise ValueError('Malformed report score')
            means=[]
            for rs, report in zip(report_rows, reports):
                subtype_means = [sum(rs[k]['score'] for k in ids if cohort[k]['question_type']==typ)/sum(cohort[k]['question_type']==typ for k in ids) for typ in types]
                mean = sum(subtype_means)/len(types)
                if not math.isclose(mean, report['groups'][name]['score'], abs_tol=1e-12): raise ValueError('Report mean differs from scores')
                means.append(report['groups'][name]['score'])
            groups[name] = dict(items=len(ids), scores_equal=sum(x==y for x,y in zip(*scores)), score_equality_share=sum(x==y for x,y in zip(*scores))/len(ids), mean_a=means[0], mean_b=means[1], mean_equal=means[0]==means[1])
        means = [r['five_category_mean']['score'] for r in reports]
        for r, mean in zip(reports, means):
            if not math.isclose(sum(r['groups'][g]['score'] for g in GROUPS)/5, mean, abs_tol=1e-12): raise ValueError('Five-category mean differs')
        equal = sum(d['tokens_equal'] for d in details)
        result['arms'][arm] = dict(items=len(details), tokens_equal=equal, token_id_equality_share=equal/len(details),
            per_item=details, categories=groups, five_category_mean_a=means[0], five_category_mean_b=means[1])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command')
    p = sub.add_parser('rv-stage'); p.add_argument('--root', default=str(T.DEFAULT_ROOT)); p.add_argument('--tar', required=True)
    for name in ('rv-proof', 'rv-read'):
        p = sub.add_parser(name); p.add_argument('--root', default=str(T.DEFAULT_ROOT)); p.add_argument('--artifact', required=True)
        p.add_argument('--sha256', required=True); p.add_argument('--frames', type=int, default=32, choices=(32,64))
        p.add_argument('--gpu', type=int, required=True); p.add_argument('--token', required=True); p.add_argument('--out', required=True)
        p.add_argument('--bwrap', default=T.DEFAULT_BWRAP)
        if name == 'rv-read': p.add_argument('--proof', required=True)
    p = sub.add_parser('rv-compare'); p.add_argument('--a', required=True); p.add_argument('--b', required=True); p.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command == 'rv-stage':
        pins_check(); root = local(args.root)
        if shutil.disk_usage(root).free < 200*1024**3 + sum(p['bytes'] for p in need_rows(KIT/'media/NEED_261.json').values()):
            raise ValueError('Staging must preserve 200 GiB free space')
        result = extract_media(local(args.tar), root/'rv_media', KIT/'media/NEED_261.json')
    elif args.command in ('rv-proof','rv-read'): result = launch(args)
    elif args.command == 'rv-compare':
        result = compare(args.a, args.b); out = local(args.out)
        if out.exists(): raise ValueError('Comparison output exists')
        T.dump(out, result)
        result = dict(output=str(out), token_id_equality_share=result['arms']['B2048']['token_id_equality_share'])
    else: parser.error('Require a command')
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__': main()
