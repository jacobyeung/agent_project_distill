def mode_limit(mode):
    if mode not in ('pilot', 'full'):
        raise ValueError('Unknown return mode')
    return 100_000_000 if mode == 'pilot' else 300_000_000


def identity(pool, token, rate=4*1024**2, synthetic=False):
    pool = Path(pool)
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or not 0 < rate <= 4*1024**2:
        raise ValueError('Invalid return identity or rate')
    if not pool.is_absolute() or '..' in pool.parts:
        raise ValueError('Invalid result pool')
    allowed = Path(__file__).resolve().parent/'test_runs' if synthetic else AUTHORIZED_POOL
    # Keep all pool filesystem operations in the deadline-bounded child.
    if (synthetic and not pool.is_relative_to(allowed)) or (not synthetic and pool != allowed):
        raise ValueError('Results require the authorized destination')
    return pool


def pool_operation(action, pool, token, local=None, timeout=60, rate=4*1024**2):
    argv = [sys.executable, '-I', '-s', '-B', str(Path(__file__).resolve()),
            '--pool-worker', action, str(pool), token, str(rate)]
    if local is not None:
        argv.append(str(local))
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.stdout.close()
        process.stderr.close()
        raise TimeoutError('Pool operation exceeded '+str(timeout)+' seconds')
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, argv, stdout, stderr)
    return json.loads(stdout)


def write_test(pool, token):
    pool = identity(pool, token)
    started = time.monotonic()
    result = pool_operation('test', pool, token, timeout=60)
    if time.monotonic()-started > 60:
        raise TimeoutError('Pool write test exceeded 60 seconds')
    if result.get('verified') is not True or result.get('bytes') != 4*1024**2:
        raise ValueError('Pool write test did not verify')
    return result


def pool_worker(action, pool, token, rate, local=None):
    pool = Path(pool)
    if pool.is_symlink() or not pool.is_absolute() or not re.fullmatch('[a-z][0-9a-f]{8,32}', token):
        raise ValueError('Invalid pool worker identity')
    pool.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(pool, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if action == 'test':
            data = os.urandom(4*1024**2)
            if usage(pool)+len(data)+EXIT_RESERVE > POOL_LIMIT:
                raise S.BudgetError('No room for pool write test within 1 GiB')
            # The OS owns the anonymous file lifetime; no other pool entry is touched.
            with tempfile.TemporaryFile(dir=pool) as stream:
                if stream.write(data) != len(data):
                    raise OSError('Short pool write')
                stream.flush()
                os.fsync(stream.fileno())
                stream.seek(0)
                actual = hashlib.sha256(stream.read()).hexdigest()
                expected = hashlib.sha256(data).hexdigest()
                if actual != expected:
                    raise ValueError('Pool write readback differs')
            return dict(verified=True, bytes=len(data), sha256=actual, deadline_seconds=60)
        if action == 'receipt':
            local = Path(local)
            dest = pool/token
            if not dest.is_dir() or dest.is_symlink():
                raise ValueError('No pool return for its receipt')
            value = json.loads((local/'RETURN_RECEIPT.json').read_text())
            exit_value = json.loads((dest/'EXIT.json').read_text())
            if (value['token'] != token or value['plan_sha256'] != exit_value['plan_sha256']
                    or value['job'] != exit_value['job']):
                raise ValueError('Pool receipt identity differs')
            size = (local/'RETURN_RECEIPT.json').stat().st_size
            if (size > EXIT_RESERVE or usage(dest)+size > mode_limit(exit_value['mode'])
                    or usage(pool)+size > POOL_LIMIT):
                raise S.BudgetError('No room for return proof')
            S.atomic_json(dest/'RETURN_RECEIPT.json', value)
            if sha(dest/'RETURN_RECEIPT.json') != sha(local/'RETURN_RECEIPT.json'):
                raise ValueError('Pool proof readback differs')
            return dict(verified=True, sha256=sha(dest/'RETURN_RECEIPT.json'))
        if action != 'publish' or not 0 < rate <= 4*1024**2:
            raise ValueError('Invalid pool worker action')
        local = Path(local)
        receipt = json.loads((local/'EXIT.json').read_text())
        names = ('result.tar.gz', 'EXIT.json', 'JOB.log')
        size = sum((local/name).stat().st_size for name in names)
        if size > mode_limit(receipt['mode']):
            raise S.BudgetError('Return exceeds mode cap')
        if usage(pool)+size+EXIT_RESERVE > POOL_LIMIT:
            raise S.BudgetError('Return exceeds 1 GiB result pool')
        dest = pool/token
        dest.mkdir(mode=0o700)
        pins = {}
        started, copied = time.monotonic(), 0
        # EXIT is committed only after its archive; a partial copy cannot admit a read.
        for name in names:
            partial = dest/(name+'.partial')
            with (local/name).open('rb') as source, partial.open('xb') as output:
                for data in iter(lambda: source.read(256*1024), b''):
                    if output.write(data) != len(data):
                        raise OSError('Short pool copy')
                    copied += len(data)
                    time.sleep(max(0, copied/rate-(time.monotonic()-started)))
                output.flush()
                os.fsync(output.fileno())
            if partial.stat().st_size != (local/name).stat().st_size or sha(partial) != sha(local/name):
                raise ValueError('Pool SHA256 readback differs')
            os.replace(partial, dest/name)
            pins[name] = dict(bytes=(dest/name).stat().st_size, sha256=sha(dest/name))
        os.fsync(fd)
        return dict(verified=True, objects=pins, bytes=size)
    finally:
        os.close(fd)


def publish(source, pool, token, plan_sha256, returncode, synthetic=False,
            rate=4*1024**2, mode='pilot', cloud_config=None):
    source, pool = Path(source), identity(pool, token, rate, synthetic)
    cap = mode_limit(mode)
    if not re.fullmatch('[0-9a-f]{64}', plan_sha256):
        raise ValueError('Invalid return plan')
    if cloud_config is None:
        cloud_config = CLOUD_CONFIG
    if not Path(cloud_config).is_absolute():
        raise ValueError('Cloud configuration must be absolute')
    local = source.parent/('r_'+token+'_'+uuid.uuid4().hex)
    local.mkdir(mode=0o700)
    complete, failed = (source/'COMPLETE.json').is_file(), (source/'FAILED.json').is_file()
    marker = json.loads((source/'COMPLETE.json').read_text()) if complete else {}
    ok = complete and not failed and returncode == 0 and marker.get('plan_sha256') == plan_sha256 and marker.get('synthetic') is synthetic
    value = dict(schema='evalx-orchard-result-return-v1', token=token, plan_sha256=plan_sha256,
        job=os.environ.get('SLURM_JOB_ID'), returncode=returncode, synthetic=synthetic,
        conflicting_terminal_markers=complete and failed, complete=ok,
        status='COMPLETE' if ok else 'FAILED', archive_complete=True, mode=mode)
    archive = local/'result.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=S.LimitedWriter(raw, min(S.ARCHIVE_LIMIT, cap-EXIT_RESERVE)),
                          mode='w:gz', compresslevel=6) as tf:
            for name, path in sorted(S.members(source).items()):
                tf.add(path, arcname=name, recursive=False)
        raw.flush()
        os.fsync(raw.fileno())
    value.update(archive=dict(name=archive.name, bytes=archive.stat().st_size, sha256=sha(archive)),
                 archive_bytes=archive.stat().st_size, archive_sha256=sha(archive))
    S.atomic_json(local/'EXIT.json', value)
    (local/'JOB.log').write_text(json.dumps(value, sort_keys=True)+'\n')
    if (local/'EXIT.json').stat().st_size > EXIT_RESERVE or usage(local) > cap:
        raise S.BudgetError('Return files exceed mode cap')
    receipt = dict(schema=1, token=token, plan_sha256=plan_sha256, job=value['job'], channels={})
    try:
        receipt['channels']['pool'] = pool_operation('publish', pool, token, local, timeout=120, rate=rate)
    except Exception as error:
        receipt['channels']['pool'] = dict(verified=False, error=str(error))
    try:
        receipt['channels']['gcs'] = upload(local, token, cloud_config=cloud_config)
    except Exception as error:
        receipt['channels']['gcs'] = dict(verified=False, error=str(error), objects=getattr(error, 'objects', {}))
    receipt['returned'] = any(c.get('verified') for c in receipt['channels'].values())
    receipt['verified_channels'] = [k for k,v in receipt['channels'].items() if v.get('verified')]
    S.atomic_json(local/'RETURN_RECEIPT.json', receipt)
    S.atomic_json(source/'RETURN_RECEIPT.json', receipt)
    proof_channels = {}
    try:
        proof_channels['pool'] = pool_operation('receipt', pool, token, local, timeout=60)
    except Exception as error:
        proof_channels['pool'] = dict(verified=False, error=str(error))
    try:
        if sum((local/n).stat().st_size for n in ('result.tar.gz','EXIT.json','JOB.log','RETURN_RECEIPT.json')) > cap:
            raise S.BudgetError('Return proof exceeds mode cap')
        proof_channels['gcs'] = upload(local, token, names=('RETURN_RECEIPT.json',), cloud_config=cloud_config)
    except Exception as error:
        proof_channels['gcs'] = dict(verified=False, error=str(error))
    S.atomic_json(source/'RETURN_PROOF.json', proof_channels)
    value.update(returned=receipt['returned'], verified_channels=receipt['verified_channels'], local_return=str(local))
    value['proof_channels'] = proof_channels
    if not receipt['returned']:
        value.update(status='INCOMPLETE', complete=False)
    return value


def fetch_return(config, submission, destination, remote):
    """Fetch through an injected Orchard command runner; authenticate either channel."""
    if submission.get('status') != 'SUBMITTED':
        raise ValueError('Reconcile uncertain submission before fetching')
    token = config['token']
    identity(AUTHORIZED_POOL, token)
    cap = mode_limit(config.get('mode', 'pilot'))
    cloud_config = config.get('assets', {}).get('gcloud_config', CLOUD_CONFIG)
    cloud = ['env', 'CLOUDSDK_CONFIG='+cloud_config, 'gcloud', 'storage']
    target = Path(destination)/'fetched'
    target.mkdir(mode=0o700, exist_ok=True)
    errors = {}
    reader = ('import sys;from pathlib import Path;p=Path(sys.argv[1]);'
              'assert not p.is_symlink() and p.stat().st_size<=int(sys.argv[2]);'
              'sys.stdout.buffer.write(p.read_bytes())')
    for channel in ('pool', 'gcs'):
        try:
            objects = {}
            def read(name, limit):
                if channel == 'pool':
                    command = ['python3', '-I', '-s', '-B', '-c', reader,
                               str(AUTHORIZED_POOL/token/name), str(limit)]
                else:
                    uri = GCS_ROOT+'/'+token+'/'+name
                    described = remote(cloud+['objects', 'describe', uri, '--format=json'])
                    if described.returncode:
                        raise ValueError('GCS metadata unavailable')
                    meta = json.loads(described.stdout)
                    generation = str(meta.get('generation', ''))
                    size = int(meta.get('size', -1))
                    if not generation.isdigit() or not 0 < size <= limit:
                        raise ValueError('Invalid GCS return metadata')
                    objects[name] = dict(generation=generation, bytes=size)
                    command = cloud+['cat', uri+'#'+generation]
                throttle = (
                    'import subprocess,sys,time\n'
                    'p=subprocess.Popen(sys.argv[2:],stdout=subprocess.PIPE)\n'
                    'start=time.monotonic();size=0;limit=int(sys.argv[1])\n'
                    'while True:\n'
                    ' data=p.stdout.read(256*1024)\n'
                    ' if not data:break\n'
                    ' size+=len(data)\n'
                    ' if size>limit:p.kill();raise ValueError("Return exceeds bound")\n'
                    ' time.sleep(max(0,size/8000000-(time.monotonic()-start)))\n'
                    ' sys.stdout.buffer.write(data);sys.stdout.buffer.flush()\n'
                    'sys.exit(p.wait())\n')
                result = remote(['python3', '-I', '-s', '-B', '-c', throttle, str(limit), *command])
                if result.returncode or len(result.stdout) > limit:
                    raise ValueError('Bounded return unavailable')
                if channel == 'gcs' and len(result.stdout) != objects[name]['bytes']:
                    raise ValueError('GCS return size differs')
                return result.stdout
            raw = read('EXIT.json', EXIT_RESERVE)
            value = json.loads(raw)
            if (value.get('token') != token or str(value.get('job')) != str(submission['job'])
                    or value.get('plan_sha256') != config['plan_sha256'] or value.get('synthetic') is not False
                    or value.get('mode', 'pilot') != config.get('mode', 'pilot')):
                raise ValueError('Returned identity differs')
            pin = value.get('archive', {})
            if (pin.get('name') != 'result.tar.gz' or type(pin.get('bytes')) is not int
                    or not 0 < pin['bytes'] <= cap-EXIT_RESERVE
                    or not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', ''))):
                raise ValueError('Missing bounded archive identity')
            data = read('result.tar.gz', pin['bytes'])
            if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
                raise ValueError('Fetched archive SHA256 differs')
            archive = target/(channel+'_'+uuid.uuid4().hex+'.tar.gz')
            archive.write_bytes(data)
            if value.get('status') == 'COMPLETE':
                verify(value, archive, config['plan_sha256'])
            os.replace(archive, target/'result.tar.gz')
            (target/'EXIT.json').write_bytes(raw)
            proof = None
            try:
                proof_raw = read('RETURN_RECEIPT.json', EXIT_RESERVE)
                proof = json.loads(proof_raw)
                if (proof.get('token') != token or proof.get('plan_sha256') != config['plan_sha256']
                        or str(proof.get('job')) != str(submission['job'])):
                    raise ValueError('Return proof identity differs')
                (target/'RETURN_RECEIPT.json').write_bytes(proof_raw)
            except Exception as error:
                proof = None
                errors['proof'] = str(error)
            result = dict(schema='evalx-orchard-fetch-v1', token=token, job=submission['job'],
                          status=value['status'], channel=channel, objects=objects,
                          archive=dict(path=str(target/'result.tar.gz'), sha256=sha(target/'result.tar.gz')),
                          fallback_errors=errors, return_proof=proof)
            S.atomic_json(target/'FETCH.json', result)
            return result
        except Exception as error:
            errors[channel] = str(error)
    raise RuntimeError('Neither return verified: '+json.dumps(errors, sort_keys=True))


if __name__ == '__main__':
    if len(sys.argv) not in (6, 7) or sys.argv[1] != '--pool-worker':
        raise SystemExit('Expected a pool worker invocation')
    print(json.dumps(pool_worker(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]),
                                 sys.argv[6] if len(sys.argv) == 7 else None)))
