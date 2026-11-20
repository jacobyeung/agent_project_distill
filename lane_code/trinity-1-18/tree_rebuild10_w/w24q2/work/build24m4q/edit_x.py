from pathlib import Path
import time
L=Path(__file__).resolve().parents[2];p=L/'out/rcj/x.py';s=p.read_text()
s=s.replace("    old_argv = sys.argv\n    sys.argv =", """    import rg
    original_regenerate = rg.regenerate
    def observed(cfg, directory, **kwargs):
        z.write(root/'ch_cfg.json', cfg)
        try:
            return original_regenerate(cfg, directory, **kwargs)
        finally:
            # Observe completed DB bytes even if a later native step refuses.
            if (Path(directory)/'selection/rows.sqlite').is_file():
                try:
                    import ch
                    ch.run(cfg, directory, root)
                except Exception as error:
                    z.write(root/'chain.json', dict(status='UNAVAILABLE',
                        reason=type(error).__name__+': '+str(error)))
    rg.regenerate = observed
    old_argv = sys.argv
    sys.argv =""")
s=s.replace("        px.resolver = original\n\n\ndef run(kit", "        px.resolver = original\n        rg.regenerate = original_regenerate\n\n\ndef run(kit")
a=s.index('\ndef publish(')
s=s[:a]+'''
HELPERS = ('n_sample.json', 'nd.json', 'na.json.gz', 'routing_types.json',
    'chain.json', 'cand_cmp.json', 'cand.json.gz',
    'pc_n.log.tail', 'pc_p.log.tail', 'rd.log.tail')


def chain_publish(kit, root, target):
    """Run before unrelated publication work; never change the job's status."""
    z = attach(kit); root, target = Path(root), Path(target)
    result = dict(status='UNAVAILABLE'); files = {}; errors = []
    try:
        if not (root/'chain.json').is_file() and (root/'ch_cfg.json').is_file():
            result['returncode'] = launch(kit, root, '', action='chain')
        if (root/'chain.json').is_file():
            result = z.load(root/'chain.json')
        else:
            z.write(root/'chain.json', result)
        for name in ('chain.json', 'cand_cmp.json', 'cand.json.gz'):
            p = root/name
            if p.is_file():
                try:
                    shutil.copyfile(p, target/name)
                    files[name] = dict(source=name, sha256=z.sha(p), size=p.stat().st_size)
                except Exception as error:
                    errors.append(dict(file=name, error=type(error).__name__+': '+str(error)))
    except Exception as error:
        result = dict(status='UNAVAILABLE', reason=type(error).__name__+': '+str(error))
    return dict(status=result.get('status', 'UNAVAILABLE'),
        routing=result.get('streams', {}).get('routing'), population=result.get('population'),
        all_streams_status=result.get('all_streams_status'), publication_errors=errors), files


def publication_size(target, timing):
    target = Path(target)
    total = sum(p.stat().st_size for p in target.rglob('*') if p.is_file() and p.name != 'timings.json')
    helper = sum((target/name).stat().st_size for name in HELPERS if (target/name).is_file())
    timing.update(publication_bytes_before_timings=total, aggregate_publication_bytes=0,
        aggregate_limit_status='PASS', helper_limit_bytes=LIMIT,
        helper_publication_bytes=0, helper_limit_status='PASS', timings_bytes=0)
    # The byte count includes its own decimal representation and status fields.
    for _ in range(32):
        size = len((json.dumps(timing, sort_keys=True, indent=2)+'\\n').encode())
        values = dict(timings_bytes=size, aggregate_publication_bytes=total+size,
            helper_publication_bytes=helper+size,
            aggregate_limit_status='PASS' if total+size < LIMIT else 'FAIL',
            helper_limit_status='PASS' if helper+size < LIMIT else 'FAIL')
        if all(timing[k] == v for k, v in values.items()):
            return
        timing.update(values)
    raise ValueError('E97:size')

'''+s[a:]
s=s.replace("    primary = native/'selection' if mode=='r' else native\n", "    primary = native/'selection' if mode=='r' else native\n    chain = None\n    if mode == 'r':\n        chain, chain_files = chain_publish(kit, root, target)\n        files.update(chain_files)\n")
s=s.replace("    if mode=='r': timing.update(task_a=dict(status='UNAVAILABLE'), routing_types='UNAVAILABLE')", "    if mode=='r': timing.update(task_a=dict(status='UNAVAILABLE'), routing_types='UNAVAILABLE', chain=chain)")
s=s.replace("    if mode=='r' and all(p.is_file() for p in bases):\n        start = time.monotonic()\n        try:\n            timing['proc_returncode']", "    if mode=='r':\n        timing['task_a']['task_iv'] = chain['status']\n        timing['task_a']['population_status'] = (chain.get('population') or {}).get('status', 'UNAVAILABLE')\n        if timing['task_a'].get('task_i') == 'PASS' and chain['status'] != 'PASS':\n            timing['task_a']['task_i'] = 'FAIL'\n        if chain['status'] != 'PASS':\n            timing['task_a']['status'] = 'FAIL'\n    if mode=='r' and all(p.is_file() for p in bases):\n        start = time.monotonic()\n        try:\n            timing['proc_returncode']")
s=s.replace("for name in ('n_sample.json','nd.json','na.json.gz','routing_types.json') if", "for name in HELPERS if")
a=s.index("            total = sum(p.stat().st_size for p in target.rglob('*')",s.index("    timing['post_returncode'] = post_rc"));b=s.index('        except Exception as error:',a)
s=s[:a]+"            publication_size(target, timing)\n"+s[b:]
s=s.replace("        elif mode == 'check':", "        elif mode == 'chain':\n            import ch\n            ch.bound(kit, root)\n        elif mode == 'check':")
old=L/'attic/build24m4q/out/rcj/x.py';old.parent.mkdir(parents=True,exist_ok=True)
if old.exists():old=old.with_name(old.name+'.'+str(time.time_ns()))
p.rename(old);p.write_text(s)
