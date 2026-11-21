"""Retain bounded CPU comparisons for authenticated failure publication."""
_comparisons=[]


def compare(name, expected, found):
    def bounded(value):
        raw=json.dumps(value,sort_keys=True)
        return value if len(raw)<=2048 else raw[:2048]
    item=dict(check=name,expected=bounded(expected),found=bounded(found),passed=expected==found)
    _comparisons.append(item)
    del _comparisons[:-16]
    if not item['passed']:
        raise ValueError(name+' expected='+json.dumps(item['expected'])+' found='+json.dumps(item['found']))


def cpu_failure(error):
    # This handler covers staging, both guards, preparation and dispatch.
    job=os.environ.get('SLURM_JOB_ID','')
    if not job.isdigit() or '--package' not in sys.argv:return
    package=Path(sys.argv[sys.argv.index('--package')+1])
    public=json.loads((package/'0.json').read_text())
    value=dict(job=job,plan=public['plan_sha256'],passed=False,
               error=(type(error).__name__+': '+str(error))[:2048],
               comparisons=_comparisons,expected=None,found=None)
    last=_comparisons[-1] if _comparisons else None
    if last:value.update(expected=last['expected'],found=last['found'])
    value['failed_check']=last['check'] if last and not last['passed'] else None
    if not last:value['comparison_status']='No comparison reached; inspect the exception'
    elif last['passed']:value['comparison_status']='Last comparison passed; the exception came later'
    if isinstance(error,subprocess.CalledProcessError):
        value.update(failed_check='Pool subprocess exit status',comparison_status='Subprocess failed',
                     expected=dict(returncode=0),found=dict(returncode=error.returncode,
                     stderr=str(error.stderr)[-2048:],stdout=str(error.stdout)[-2048:]))
    # One write keeps the metadata ledger to a single charge.
    with (package/'a/30.json').open('w') as stream:stream.write(json.dumps(value))
