from common import *
import shutil
src=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/ps/ps.py')
assert J.sha(src).startswith('6945292e')
replace(L/'out/rcj/ps.py',src.read_bytes())
request=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_review/evidence/n_review1d/P_SAMPLE_I.json')
replace(L/'out/rcj/P_SAMPLE_I.json',request.read_bytes())
p=L/'out/rcj/x.py';s=p.read_text();a=s.index('def sample(');b=s.index('\n\ndef rdiff',a)
s=s[:a]+'''def sample(database, request, output, rd0=None):
    script = Path(__file__).with_name('ps.py')
    # The public helper always supplies the complete production gate.
    env = {**os.environ, 'PS_GATE': DB}
    result = subprocess.run([sys.executable, '-I', '-s', '-B', str(script), str(database),
                             str(request), str(rd0) if rd0 else '-', str(output)],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if result.returncode:
        raise ValueError(result.stdout.strip())
    value = json.loads(Path(output).read_bytes())
    return dict(status='PASS', rows=len(value['rows']), bytes=Path(output).stat().st_size,
                request_sha256=value['request_sha256'])
''' +s[b:]
a=s.index("    request = target.parents[1]/'rcj/P_SAMPLE_I.json'");b=s.index("    if mode=='r' and gate",a)
s=s[:a]+s[b:]
point="    for key, filename in (('staging_seconds','staging.json'),"
at=s.index(point)
s=s[:at]+'''    # Sampling follows comparison and cannot change either mode's status.
    request = target.parents[1]/'rcj/P_SAMPLE_I.json'
    if request.is_file():
        try:
            if gate: timing['sample'] = sample(bases[0], request, target/'p_sample.json', target/'rd0' if mode=='r' else None)
            else: timing['sample'] = dict(status='SKIPPED', reason='R1_SAMPLE_GATE_FAILED')
        except Exception as error:
            timing['sample'] = dict(status='REFUSE', reason=str(error))
    if mode=='r' and all(p.is_file() for p in bases):
        start = time.monotonic()
        try:
            timing['proc_returncode'] = launch(kit, root, job, action='check')
            result = root/'proc_check.json'
            if result.is_file():
                shutil.copyfile(result, target/'proc_check.json')
                files['proc_check.json'] = dict(source='proc_check.json', sha256=z.sha(result), size=result.stat().st_size)
                if z.load(result).get('status')!='PASS': post_rc = 1
            else:
                z.write(target/'proc_check.json', dict(status='FAIL', reason='E95'))
                post_rc = 1
            if timing['proc_returncode']: post_rc = 1
        except Exception as error:
            timing['proc_refusal'] = type(error).__name__+':'+str(error); post_rc = 1
            try: z.write(target/'proc_check.json', dict(status='FAIL', reason=timing['proc_refusal']))
            except Exception as failure: errors.append(dict(file='proc_check.json', error=type(failure).__name__))
        finally: timing['proc_seconds'] = time.monotonic()-start
    elif mode=='r': timing['proc_status'] = 'UNAVAILABLE'
''' +s[at:]
s=s.replace("        elif mode == 'publish':", "        elif mode == 'check':\n            import pc\n            raise SystemExit(pc.run(kit, root))\n        elif mode == 'publish':")
replace(p,s)
# Keep both mount fixes and the exact scheduler/resource contract.
assert J.sha(L/'out/rcj/rcj.sh')==J.load(D/'BASE_RCJ.json')['rcj.sh']['sha256']
print('Sample reference',J.sha(L/'out/rcj/ps.py'),'request',J.sha(L/'out/rcj/P_SAMPLE_I.json'))
