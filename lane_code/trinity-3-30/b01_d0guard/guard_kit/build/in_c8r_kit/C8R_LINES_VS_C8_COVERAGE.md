# C8r lines added vs C8, and where each is executed
Columns: P = C8r whole-worker pilot rehearsal (builds/02_c8r/work/rh_pilot_op2, out/coverage/pilot), T = C8r unit tests (out/coverage/tests), F = C8 full rehearsal (same line number only if file unchanged). Non-code lines (blank, comment, docstring, JSON) are listed as "-".

## orchard_launcher.py

| line | P | T | text |
|---:|---|---|---|
| 365 |  | x | `return R.fetch_return(config, submission, destination, remote)` |

## orchard_native/native_job.py

| line | P | T | text |
|---:|---|---|---|
| 190 |  | x | `evidence["pool_write_test"] = R.write_test(R.AUTHORIZED_POOL, config["token"])` |
| 260 |  | x | `result = R.publish(source, R.AUTHORIZED_POOL, config["token"], config["plan_sha256"], code` |
| 261 | - | - | `mode=config["mode"], cloud_config=config["assets"]["gcloud_config"])` |

## orchard_native/native_launcher.py

| line | P | T | text |
|---:|---|---|---|
| 24 |  | x | `DIRECT_DIGEST = "20fa48869e0689ac200405895b1811811d7dc092bec6d6a500069714b1f40117"` |
| 63 |  |  | `return_bytes=100_000_000 if mode == "pilot" else 300_000_000, pool_bytes=1024**3)` |

## orchard_native/native_local_check.py

| line | P | T | text |
|---:|---|---|---|
| 30 |  | x | `PACKAGING |= {str(C.LOGICAL_ROOT / name) for name in ("orchard_results.py", "orchard_launc` |

## orchard_native/native_metrics.py

| line | P | T | text |
|---:|---|---|---|
| 21 | x | x | `RETURN_LIMIT = 300_000_000-16*1024` |

## orchard_results.py

| line | P | T | text |
|---:|---|---|---|
| 1 | x | x | `"""Bounded independent returns, ported from the accepted lane transport."""` |
| 8 | x | x | `import subprocess` |
| 9 | x | x | `import sys` |
| 11 | x | x | `import tempfile` |
| 14 | x | x | `sys.path.insert(0, str(Path(__file__).resolve().parent))` |
| 17 | x | x | `AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/n2r')` |
| 18 | x | x | `GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/n2r'` |
| 19 | x | x | `CLOUD_CONFIG = '/project/community/jjyeung/gcloud'` |
| 20 | x | x | `READ_LIMIT = 300_000_000` |
| 37 | x | x | `class UploadError(ValueError):` |
| 38 | x | x | `def __init__(self,error,objects):` |
| 39 |  | x | `super().__init__(str(error));self.objects=objects` |
| 40 | - | - | `` |
| 41 | - | - | `` |
| 42 | x | x | `def upload(local,token,names=('result.tar.gz','EXIT.json'),cloud_config=None):` |
| 43 | x | x | `env=dict(os.environ,CLOUDSDK_CONFIG=cloud_config or CLOUD_CONFIG);objects={}` |
| 44 | x | x | `try:` |
| 45 | x | x | `for name in names:` |
| 46 | x | x | `path=Path(local)/name;uri=GCS_ROOT+'/'+token+'/'+name` |
| 47 | x | x | `objects[name]=dict(uri=uri,generation=None,sha256=sha(path),bytes=path.stat().st_size,veri` |
| 48 | x | x | `subprocess.run(['gcloud','storage','cp',str(path),uri],env=env,check=True,` |
| 49 | - | - | `capture_output=True,timeout=180)` |
| 50 | x | x | `described=subprocess.run(['gcloud','storage','objects','describe',uri,'--format=json'],` |
| 51 | - | - | `env=env,check=True,capture_output=True,text=True,timeout=60)` |
| 52 | x | x | `meta=json.loads(described.stdout);generation=str(meta.get('generation',''))` |
| 53 | x | x | `if not generation.isdigit() or int(meta.get('size',-1))!=path.stat().st_size:` |
| 54 |  | x | `raise ValueError('GCS object metadata differs')` |
| 55 | x | x | `objects[name]['generation']=generation` |
| 56 | x | x | `check=Path(local)/(name+'.gcs-check')` |
| 57 | x | x | `with check.open('xb') as out:` |
| 58 | x | x | `subprocess.run(['gcloud','storage','cat',uri+'#'+generation],env=env,check=True,` |
| 59 | - | - | `stdout=out,stderr=subprocess.PIPE,timeout=180)` |
| 60 | x | x | `digest=sha(check)` |
| 61 | x | x | `if check.stat().st_size!=path.stat().st_size or digest!=sha(path):` |
| 62 |  | x | `raise ValueError('GCS object SHA256 differs')` |
| 63 | x | x | `objects[name]['verified']=True` |
| 64 | x | x | `with (Path(local)/'JOB.log').open('a') as log:` |
| 65 | x | x | `log.write(json.dumps(dict(upload=objects[name]),sort_keys=True)+'\n')` |
| 66 |  | x | `except Exception as error:` |
| 67 |  | x | `with (Path(local)/'JOB.log').open('a') as log:` |
| 68 |  | x | `log.write(json.dumps(dict(upload_error=str(error),objects=objects),sort_keys=True)+'\n')` |
| 69 |  | x | `raise UploadError(error,objects) from error` |
| 70 | x | x | `return dict(verified=True,objects=objects)` |
| 85 | - | - | `or archive.stat().st_size > mode_limit(receipt.get('mode', 'pilot'))-EXIT_RESERVE or sha(a` |
| 104 | - | - | `` |
| 105 | x | x | `def mode_limit(mode):` |
| 106 | x | x | `if mode not in ('pilot', 'full'):` |
| 107 |  | x | `raise ValueError('Unknown return mode')` |
| 108 | x | x | `return 100_000_000 if mode == 'pilot' else 300_000_000` |
| 109 | - | - | `` |
| 110 | - | - | `` |
| 111 | x | x | `def identity(pool, token, rate=4*1024**2, synthetic=False):` |
| 112 | x | x | `pool = Path(pool)` |
| 113 | x | x | `if not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or not 0 < rate <= 4*1024**2:` |
| 114 |  | x | `raise ValueError('Invalid return identity or rate')` |
| 115 | x | x | `if not pool.is_absolute() or '..' in pool.parts:` |
| 116 |  | x | `raise ValueError('Invalid result pool')` |
| 117 | x | x | `allowed = Path(__file__).resolve().parent/'test_runs' if synthetic else AUTHORIZED_POOL` |
| 118 | - | - | `# Keep all pool filesystem operations in the deadline-bounded child.` |
| 119 | x | x | `if (synthetic and not pool.is_relative_to(allowed)) or (not synthetic and pool != allowed)` |
| 120 |  | x | `raise ValueError('Results require the authorized destination')` |
| 121 | x | x | `return pool` |
| 122 | - | - | `` |
| 123 | - | - | `` |
| 124 | x | x | `def pool_operation(action, pool, token, local=None, timeout=60, rate=4*1024**2):` |
| 125 | x | x | `argv = [sys.executable, '-I', '-s', '-B', str(Path(__file__).resolve()),` |
| 126 | - | - | `'--pool-worker', action, str(pool), token, str(rate)]` |
| 127 | x | x | `if local is not None:` |
| 128 | x | x | `argv.append(str(local))` |
| 129 | x | x | `process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True` |
| 130 | x | x | `try:` |
| 131 | x | x | `stdout, stderr = process.communicate(timeout=timeout)` |
| 132 |  | x | `except subprocess.TimeoutExpired:` |
| 133 |  | x | `process.kill()` |
| 134 |  | x | `process.stdout.close()` |
| 135 |  | x | `process.stderr.close()` |
| 136 |  | x | `raise TimeoutError('Pool operation exceeded '+str(timeout)+' seconds')` |
| 137 | x | x | `if process.returncode:` |
| 138 |  | x | `raise subprocess.CalledProcessError(process.returncode, argv, stdout, stderr)` |
| 139 | x | x | `return json.loads(stdout)` |
| 140 | - | - | `` |
| 141 | - | - | `` |
| 142 | x | x | `def write_test(pool, token):` |
| 143 | x | x | `pool = identity(pool, token)` |
| 144 | x | x | `started = time.monotonic()` |
| 145 | x | x | `result = pool_operation('test', pool, token, timeout=60)` |
| 146 | x | x | `if time.monotonic()-started > 60:` |
| 147 |  | x | `raise TimeoutError('Pool write test exceeded 60 seconds')` |
| 148 | x | x | `if result.get('verified') is not True or result.get('bytes') != 4*1024**2:` |
| 149 |  | x | `raise ValueError('Pool write test did not verify')` |
| 150 | x | x | `return result` |
| 151 | - | - | `` |
| 152 | - | - | `` |
| 153 | x | x | `def pool_worker(action, pool, token, rate, local=None):` |
| 154 |  | x | `pool = Path(pool)` |
| 155 |  | x | `if pool.is_symlink() or not pool.is_absolute() or not re.fullmatch('[a-z][0-9a-f]{8,32}', ` |
| 156 |  | x | `raise ValueError('Invalid pool worker identity')` |
| 157 |  | x | `pool.mkdir(mode=0o700, exist_ok=True)` |
| 158 |  | x | `fd = os.open(pool, os.O_RDONLY | os.O_DIRECTORY)` |
| 159 |  | x | `try:` |
| 160 |  | x | `fcntl.flock(fd, fcntl.LOCK_EX)` |
| 161 |  | x | `if action == 'test':` |
| 162 |  | x | `data = os.urandom(4*1024**2)` |
| 163 |  | x | `if usage(pool)+len(data)+EXIT_RESERVE > POOL_LIMIT:` |
| 164 |  | x | `raise S.BudgetError('No room for pool write test within 1 GiB')` |
| 165 | - | - | `# The OS owns the anonymous file lifetime; no other pool entry is touched.` |
| 166 |  | x | `with tempfile.TemporaryFile(dir=pool) as stream:` |
| 167 |  | x | `if stream.write(data) != len(data):` |
| 168 |  | x | `raise OSError('Short pool write')` |
| 169 |  | x | `stream.flush()` |
| 170 |  | x | `os.fsync(stream.fileno())` |
| 171 |  | x | `stream.seek(0)` |
| 172 |  | x | `actual = hashlib.sha256(stream.read()).hexdigest()` |
| 173 |  | x | `expected = hashlib.sha256(data).hexdigest()` |
| 174 |  | x | `if actual != expected:` |
| 175 |  | x | `raise ValueError('Pool write readback differs')` |
| 176 |  | x | `return dict(verified=True, bytes=len(data), sha256=actual, deadline_seconds=60)` |
| 177 |  | x | `if action == 'receipt':` |
| 178 |  | x | `local = Path(local)` |
| 179 |  | x | `dest = pool/token` |
| 180 |  | x | `if not dest.is_dir() or dest.is_symlink():` |
| 181 |  | x | `raise ValueError('No pool return for its receipt')` |
| 182 |  | x | `value = json.loads((local/'RETURN_RECEIPT.json').read_text())` |
| 183 |  | x | `exit_value = json.loads((dest/'EXIT.json').read_text())` |
| 184 |  | x | `if (value['token'] != token or value['plan_sha256'] != exit_value['plan_sha256']` |
| 185 | - | - | `or value['job'] != exit_value['job']):` |
| 186 |  | x | `raise ValueError('Pool receipt identity differs')` |
| 187 |  | x | `size = (local/'RETURN_RECEIPT.json').stat().st_size` |
| 188 |  | x | `if (size > EXIT_RESERVE or usage(dest)+size > mode_limit(exit_value['mode'])` |
| 189 | - | - | `or usage(pool)+size > POOL_LIMIT):` |
| 190 |  | x | `raise S.BudgetError('No room for return proof')` |
| 191 |  | x | `S.atomic_json(dest/'RETURN_RECEIPT.json', value)` |
| 192 |  | x | `if sha(dest/'RETURN_RECEIPT.json') != sha(local/'RETURN_RECEIPT.json'):` |
| 193 |  | x | `raise ValueError('Pool proof readback differs')` |
| 194 |  | x | `return dict(verified=True, sha256=sha(dest/'RETURN_RECEIPT.json'))` |
| 195 |  | x | `if action != 'publish' or not 0 < rate <= 4*1024**2:` |
| 196 |  | x | `raise ValueError('Invalid pool worker action')` |
| 197 |  | x | `local = Path(local)` |
| 198 |  | x | `receipt = json.loads((local/'EXIT.json').read_text())` |
| 199 |  | x | `names = ('result.tar.gz', 'EXIT.json', 'JOB.log')` |
| 200 |  | x | `size = sum((local/name).stat().st_size for name in names)` |
| 201 |  | x | `if size > mode_limit(receipt['mode']):` |
| 202 |  | x | `raise S.BudgetError('Return exceeds mode cap')` |
| 203 |  | x | `if usage(pool)+size+EXIT_RESERVE > POOL_LIMIT:` |
| 204 |  | x | `raise S.BudgetError('Return exceeds 1 GiB result pool')` |
| 205 |  | x | `dest = pool/token` |
| 206 |  | x | `dest.mkdir(mode=0o700)` |
| 207 |  | x | `pins = {}` |
| 208 |  | x | `started, copied = time.monotonic(), 0` |
| 209 | - | - | `# EXIT is committed only after its archive; a partial copy cannot admit a read.` |
| 210 |  | x | `for name in names:` |
| 211 |  | x | `partial = dest/(name+'.partial')` |
| 212 |  | x | `with (local/name).open('rb') as source, partial.open('xb') as output:` |
| 213 |  | x | `for data in iter(lambda: source.read(256*1024), b''):` |
| 214 |  | x | `if output.write(data) != len(data):` |
| 215 |  | x | `raise OSError('Short pool copy')` |
| 216 |  | x | `copied += len(data)` |
| 217 |  | x | `time.sleep(max(0, copied/rate-(time.monotonic()-started)))` |
| 218 |  | x | `output.flush()` |
| 219 |  | x | `os.fsync(output.fileno())` |
| 220 |  | x | `if partial.stat().st_size != (local/name).stat().st_size or sha(partial) != sha(local/name` |
| 221 |  | x | `raise ValueError('Pool SHA256 readback differs')` |
| 222 |  | x | `os.replace(partial, dest/name)` |
| 223 |  | x | `pins[name] = dict(bytes=(dest/name).stat().st_size, sha256=sha(dest/name))` |
| 224 |  | x | `os.fsync(fd)` |
| 225 |  | x | `return dict(verified=True, objects=pins, bytes=size)` |
| 226 | - | - | `finally:` |
| 227 |  | x | `os.close(fd)` |
| 228 | - | - | `` |
| 229 | - | - | `` |
| 230 | x | x | `def publish(source, pool, token, plan_sha256, returncode, synthetic=False,` |
| 231 | - | - | `rate=4*1024**2, mode='pilot', cloud_config=None):` |
| 232 | x | x | `source, pool = Path(source), identity(pool, token, rate, synthetic)` |
| 233 | x | x | `cap = mode_limit(mode)` |
| 234 | x | x | `if not re.fullmatch('[0-9a-f]{64}', plan_sha256):` |
| 235 |  | x | `raise ValueError('Invalid return plan')` |
| 236 | x | x | `if cloud_config is None:` |
| 237 |  | x | `cloud_config = CLOUD_CONFIG` |
| 238 | x | x | `if not Path(cloud_config).is_absolute():` |
| 239 |  | x | `raise ValueError('Cloud configuration must be absolute')` |
| 240 | x | x | `local = source.parent/('r_'+token+'_'+uuid.uuid4().hex)` |
| 241 | x | x | `local.mkdir(mode=0o700)` |
| 242 | x | x | `complete, failed = (source/'COMPLETE.json').is_file(), (source/'FAILED.json').is_file()` |
| 243 | x | x | `marker = json.loads((source/'COMPLETE.json').read_text()) if complete else {}` |
| 244 | x | x | `ok = complete and not failed and returncode == 0 and marker.get('plan_sha256') == plan_sha` |
| 245 | x | x | `value = dict(schema='evalx-orchard-result-return-v1', token=token, plan_sha256=plan_sha256` |
| 246 | - | - | `job=os.environ.get('SLURM_JOB_ID'), returncode=returncode, synthetic=synthetic,` |
| 247 | - | - | `conflicting_terminal_markers=complete and failed, complete=ok,` |
| 248 | - | - | `status='COMPLETE' if ok else 'FAILED', archive_complete=True, mode=mode)` |
| 249 | x | x | `archive = local/'result.tar.gz'` |
| 250 | x | x | `with archive.open('xb') as raw:` |
| 251 | x | x | `with tarfile.open(fileobj=S.LimitedWriter(raw, min(S.ARCHIVE_LIMIT, cap-EXIT_RESERVE)),` |
| 252 | - | - | `mode='w:gz', compresslevel=6) as tf:` |
| 253 | x | x | `for name, path in sorted(S.members(source).items()):` |
| 254 | x | x | `tf.add(path, arcname=name, recursive=False)` |
| 255 | x | x | `raw.flush()` |
| 256 | x | x | `os.fsync(raw.fileno())` |
| 257 | x | x | `value.update(archive=dict(name=archive.name, bytes=archive.stat().st_size, sha256=sha(arch` |
| 258 | - | - | `archive_bytes=archive.stat().st_size, archive_sha256=sha(archive))` |
| 259 | x | x | `S.atomic_json(local/'EXIT.json', value)` |
| 260 | x | x | `(local/'JOB.log').write_text(json.dumps(value, sort_keys=True)+'\n')` |
| 261 | x | x | `if (local/'EXIT.json').stat().st_size > EXIT_RESERVE or usage(local) > cap:` |
| 262 |  | x | `raise S.BudgetError('Return files exceed mode cap')` |
| 263 | x | x | `receipt = dict(schema=1, token=token, plan_sha256=plan_sha256, job=value['job'], channels=` |
| 264 | x | x | `try:` |
| 265 | x | x | `receipt['channels']['pool'] = pool_operation('publish', pool, token, local, timeout=120, r` |
| 266 |  | x | `except Exception as error:` |
| 267 |  | x | `receipt['channels']['pool'] = dict(verified=False, error=str(error))` |
| 268 | x | x | `try:` |
| 269 | x | x | `receipt['channels']['gcs'] = upload(local, token, cloud_config=cloud_config)` |
| 270 |  | x | `except Exception as error:` |
| 271 |  | x | `receipt['channels']['gcs'] = dict(verified=False, error=str(error), objects=getattr(error,` |
| 272 | x | x | `receipt['returned'] = any(c.get('verified') for c in receipt['channels'].values())` |
| 273 | x | x | `receipt['verified_channels'] = [k for k,v in receipt['channels'].items() if v.get('verifie` |
| 274 | x | x | `S.atomic_json(local/'RETURN_RECEIPT.json', receipt)` |
| 275 | x | x | `S.atomic_json(source/'RETURN_RECEIPT.json', receipt)` |
| 276 | x | x | `proof_channels = {}` |
| 277 | x | x | `try:` |
| 278 | x | x | `proof_channels['pool'] = pool_operation('receipt', pool, token, local, timeout=60)` |
| 279 |  | x | `except Exception as error:` |
| 280 |  | x | `proof_channels['pool'] = dict(verified=False, error=str(error))` |
| 281 | x | x | `try:` |
| 282 | x | x | `if sum((local/n).stat().st_size for n in ('result.tar.gz','EXIT.json','JOB.log','RETURN_RE` |
| 283 |  | x | `raise S.BudgetError('Return proof exceeds mode cap')` |
| 284 | x | x | `proof_channels['gcs'] = upload(local, token, names=('RETURN_RECEIPT.json',), cloud_config=` |
| 285 |  | x | `except Exception as error:` |
| 286 |  | x | `proof_channels['gcs'] = dict(verified=False, error=str(error))` |
| 287 | x | x | `S.atomic_json(source/'RETURN_PROOF.json', proof_channels)` |
| 288 | x | x | `value.update(returned=receipt['returned'], verified_channels=receipt['verified_channels'],` |
| 289 | x | x | `value['proof_channels'] = proof_channels` |
| 290 | x | x | `if not receipt['returned']:` |
| 291 |  | x | `value.update(status='INCOMPLETE', complete=False)` |
| 292 | x | x | `return value` |
| 293 | - | - | `` |
| 294 | - | - | `` |
| 295 | x | x | `def fetch_return(config, submission, destination, remote):` |
| 296 | - | - | `"""Fetch through an injected Orchard command runner; authenticate either channel."""` |
| 297 |  | x | `if submission.get('status') != 'SUBMITTED':` |
| 298 |  | x | `raise ValueError('Reconcile uncertain submission before fetching')` |
| 299 |  | x | `token = config['token']` |
| 300 |  | x | `identity(AUTHORIZED_POOL, token)` |
| 301 |  | x | `cap = mode_limit(config.get('mode', 'pilot'))` |
| 302 |  | x | `cloud_config = config.get('assets', {}).get('gcloud_config', CLOUD_CONFIG)` |
| 303 |  | x | `cloud = ['env', 'CLOUDSDK_CONFIG='+cloud_config, 'gcloud', 'storage']` |
| 304 |  | x | `target = Path(destination)/'fetched'` |
| 305 |  | x | `target.mkdir(mode=0o700, exist_ok=True)` |
| 306 |  | x | `errors = {}` |
| 307 |  | x | `reader = ('import sys;from pathlib import Path;p=Path(sys.argv[1]);'` |
| 308 | - | - | `'assert not p.is_symlink() and p.stat().st_size<=int(sys.argv[2]);'` |
| 309 | - | - | `'sys.stdout.buffer.write(p.read_bytes())')` |
| 310 |  | x | `for channel in ('pool', 'gcs'):` |
| 311 |  | x | `try:` |
| 312 |  | x | `objects = {}` |
| 313 |  | x | `def read(name, limit):` |
| 314 |  | x | `if channel == 'pool':` |
| 315 |  | x | `command = ['python3', '-I', '-s', '-B', '-c', reader,` |
| 316 | - | - | `str(AUTHORIZED_POOL/token/name), str(limit)]` |
| 317 | - | - | `else:` |
| 318 |  | x | `uri = GCS_ROOT+'/'+token+'/'+name` |
| 319 |  | x | `described = remote(cloud+['objects', 'describe', uri, '--format=json'])` |
| 320 |  | x | `if described.returncode:` |
| 321 |  | x | `raise ValueError('GCS metadata unavailable')` |
| 322 |  | x | `meta = json.loads(described.stdout)` |
| 323 |  | x | `generation = str(meta.get('generation', ''))` |
| 324 |  | x | `size = int(meta.get('size', -1))` |
| 325 |  | x | `if not generation.isdigit() or not 0 < size <= limit:` |
| 326 |  | x | `raise ValueError('Invalid GCS return metadata')` |
| 327 |  | x | `objects[name] = dict(generation=generation, bytes=size)` |
| 328 |  | x | `command = cloud+['cat', uri+'#'+generation]` |
| 329 |  | x | `throttle = (` |
| 330 | - | - | `'import subprocess,sys,time\n'` |
| 331 | - | - | `'p=subprocess.Popen(sys.argv[2:],stdout=subprocess.PIPE)\n'` |
| 332 | - | - | `'start=time.monotonic();size=0;limit=int(sys.argv[1])\n'` |
| 333 | - | - | `'while True:\n'` |
| 334 | - | - | `' data=p.stdout.read(256*1024)\n'` |
| 335 | - | - | `' if not data:break\n'` |
| 336 | - | - | `' size+=len(data)\n'` |
| 337 | - | - | `' if size>limit:p.kill();raise ValueError("Return exceeds bound")\n'` |
| 338 | - | - | `' time.sleep(max(0,size/8000000-(time.monotonic()-start)))\n'` |
| 339 | - | - | `' sys.stdout.buffer.write(data);sys.stdout.buffer.flush()\n'` |
| 340 | - | - | `'sys.exit(p.wait())\n')` |
| 341 |  | x | `result = remote(['python3', '-I', '-s', '-B', '-c', throttle, str(limit), *command])` |
| 342 |  | x | `if result.returncode or len(result.stdout) > limit:` |
| 343 |  | x | `raise ValueError('Bounded return unavailable')` |
| 344 |  | x | `if channel == 'gcs' and len(result.stdout) != objects[name]['bytes']:` |
| 345 |  | x | `raise ValueError('GCS return size differs')` |
| 346 |  | x | `return result.stdout` |
| 347 |  | x | `raw = read('EXIT.json', EXIT_RESERVE)` |
| 348 |  | x | `value = json.loads(raw)` |
| 349 |  | x | `if (value.get('token') != token or str(value.get('job')) != str(submission['job'])` |
| 350 | - | - | `or value.get('plan_sha256') != config['plan_sha256'] or value.get('synthetic') is not Fals` |
| 351 | - | - | `or value.get('mode', 'pilot') != config.get('mode', 'pilot')):` |
| 352 |  | x | `raise ValueError('Returned identity differs')` |
| 353 |  | x | `pin = value.get('archive', {})` |
| 354 |  | x | `if (pin.get('name') != 'result.tar.gz' or type(pin.get('bytes')) is not int` |
| 355 | - | - | `or not 0 < pin['bytes'] <= cap-EXIT_RESERVE` |
| 356 | - | - | `or not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', ''))):` |
| 357 |  | x | `raise ValueError('Missing bounded archive identity')` |
| 358 |  | x | `data = read('result.tar.gz', pin['bytes'])` |
| 359 |  | x | `if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:` |
| 360 |  | x | `raise ValueError('Fetched archive SHA256 differs')` |
| 361 |  | x | `archive = target/(channel+'_'+uuid.uuid4().hex+'.tar.gz')` |
| 362 |  | x | `archive.write_bytes(data)` |
| 363 |  | x | `if value.get('status') == 'COMPLETE':` |
| 364 |  | x | `verify(value, archive, config['plan_sha256'])` |
| 365 |  | x | `os.replace(archive, target/'result.tar.gz')` |
| 366 |  | x | `(target/'EXIT.json').write_bytes(raw)` |
| 367 |  | x | `proof = None` |
| 368 |  | x | `try:` |
| 369 |  | x | `proof_raw = read('RETURN_RECEIPT.json', EXIT_RESERVE)` |
| 370 |  | x | `proof = json.loads(proof_raw)` |
| 371 |  | x | `if (proof.get('token') != token or proof.get('plan_sha256') != config['plan_sha256']` |
| 372 | - | - | `or str(proof.get('job')) != str(submission['job'])):` |
| 373 |  | x | `raise ValueError('Return proof identity differs')` |
| 374 |  | x | `(target/'RETURN_RECEIPT.json').write_bytes(proof_raw)` |
| 375 |  | x | `except Exception as error:` |
| 376 |  | x | `proof = None` |
| 377 |  | x | `errors['proof'] = str(error)` |
| 378 |  | x | `result = dict(schema='evalx-orchard-fetch-v1', token=token, job=submission['job'],` |
| 379 | - | - | `status=value['status'], channel=channel, objects=objects,` |
| 380 | - | - | `archive=dict(path=str(target/'result.tar.gz'), sha256=sha(target/'result.tar.gz')),` |
| 381 | - | - | `fallback_errors=errors, return_proof=proof)` |
| 382 |  | x | `S.atomic_json(target/'FETCH.json', result)` |
| 383 |  | x | `return result` |
| 384 |  | x | `except Exception as error:` |
| 385 |  | x | `errors[channel] = str(error)` |
| 386 |  | x | `raise RuntimeError('Neither return verified: '+json.dumps(errors, sort_keys=True))` |
| 387 | - | - | `` |
| 388 | - | - | `` |
| 389 | x | x | `if __name__ == '__main__':` |
| 390 |  | x | `if len(sys.argv) not in (6, 7) or sys.argv[1] != '--pool-worker':` |
| 391 |  | x | `raise SystemExit('Expected a pool worker invocation')` |
| 392 |  | x | `print(json.dumps(pool_worker(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]),` |
| 393 | - | - | `sys.argv[6] if len(sys.argv) == 7 else None)))` |


Totals over statement lines: {'code': 282, 'P': 104, 'T': 281, 'none': 1}
