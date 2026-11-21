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
    if _comparisons:
        value.update(expected=_comparisons[-1]['expected'],found=_comparisons[-1]['found'])
    else:
        value['comparison_status']='No comparison reached; inspect the exception'
    if isinstance(error,subprocess.CalledProcessError):
        value.update(expected=dict(returncode=0),found=dict(returncode=error.returncode,
                     stderr=str(error.stderr)[-2048:],stdout=str(error.stdout)[-2048:]))
    with (package/'a/30.json').open('w') as stream:json.dump(value,stream)
