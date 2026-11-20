from common import *
p=L/'out/rcj/rcj.sh';s=p.read_text().replace('"$H/x.py" stage "$ROOT" "$N" "$SLURM_JOB_ID"','"$H/x.py" stage "$ROOT" "$N" "$SLURM_JOB_ID" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"').replace('"$H/x.py" launch "$ROOT" "$N" "$SLURM_JOB_ID"','"$H/x.py" launch "$ROOT" "$N" "$SLURM_JOB_ID" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"');replace(p,s);p.chmod(0o755)
p=L/'out/rcj/x.py';s=p.read_text().replace("paths=[str(self.root/'np'), str(overlay)]","paths=[str(overlay), str(self.root/'np')]")
s=s.replace('def run(kit, root):','def run(kit, root, job):').replace("elif mode == 'run': run(kit, root)","elif mode == 'run': run(kit, root, job)")
s=s.replace("    result = dict(status='REFUSE')\n    try:","    result = dict(status='REFUSE'); failure = None\n    try:")
s=s.replace("        result['refusal'] = type(error).__name__\n        raise","        result['refusal'] = type(error).__name__\n        failure = error")
s=s.replace("        z.write(root/'build.json', result)","        z.write(root/'build.json', result)\n        publish(kit, root, job, 1 if failure else 0)\n    if failure is not None:\n        raise failure")
a=s.index("    files = {}\n",s.index('def publish('));b=s.index('\n    return 0',a)
s=s[:a]+'''    files, errors = {}, []
    for name, p in (('receipt.json', root/'r/receipt.json'), ('materialization.json', root/'r/materialization.json'),
                    ('import_probe.json', root/'r_imports.json')):
        try:
            if p.is_file():
                shutil.copyfile(p, target/name)
                files[name] = dict(sha256=z.sha(p), size=p.stat().st_size)
            else:
                z.write(target/name, dict(status='UNAVAILABLE', returncode=int(rc)))
        except Exception as error:
            errors.append(dict(file=name, error=type(error).__name__))
    rows = []
    p = root/'r/rows.sqlite'
    try:
        if p.is_file():
            with p.open('rb') as f: header = f.read(16).hex()
            rows.append(dict(path='r/rows.sqlite', sha256=z.sha(p), size=p.stat().st_size, header=header))
        z.write(target/'db_bytes.json', dict(files=rows, expected='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'))
    except Exception as error:
        errors.append(dict(file='db_bytes.json', error=type(error).__name__))
    timing = dict(returncode=int(rc), files=files, publication_errors=errors)
    for key, filename in (('staging_seconds','staging.json'), ('build_seconds','build.json')):
        try:
            p = root/filename
            timing[key] = z.load(p)['seconds'] if p.is_file() else None
        except Exception as error:
            timing[key] = None
            errors.append(dict(file=filename, error=type(error).__name__))
    z.write(target/'timings.json', timing)
    if errors:
        raise ValueError('R1_PUBLICATION_INCOMPLETE')'''+s[b:]
replace(p,s)
