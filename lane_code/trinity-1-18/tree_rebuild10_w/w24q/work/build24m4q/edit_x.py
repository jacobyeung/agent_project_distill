import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=L/'out/rcj/x.py';s=p.read_text()
s=s.replace("    finally:\n        result['seconds'] = time.monotonic()-start", "    finally:\n        if mode == 'r' and (root/'dr/p/q/selection/rows.sqlite').is_file():\n            # The diagnostic must survive later publication failures.\n            try:\n                import ch\n                ch.run(kit, root)\n            except Exception as error:\n                z.write(root/'chain.json', dict(status='FAIL', reason=type(error).__name__+':'+str(error)))\n        result['seconds'] = time.monotonic()-start")
# Independent fallback runs before any publication enumerator can fail.
s=s.replace("    if mode=='r':\n        entries.append(('routing_selection.json'", "    chain_value = None\n    if mode=='r':\n        if (native/'selection/rows.sqlite').is_file() and not (root/'chain.json').is_file():\n            try: launch(kit, root, job, action='chain')\n            except Exception as error:\n                chain_value = dict(status='FAIL', reason=type(error).__name__+':'+str(error))\n        if (root/'chain.json').is_file():\n            try: chain_value = z.load(root/'chain.json')\n            except Exception as error: chain_value = dict(status='FAIL',reason=type(error).__name__)\n        if chain_value is None: chain_value = dict(status='UNAVAILABLE')\n        entries += [('chain.json', root/'chain.json'), ('cc.json.gz', root/'cc.json.gz')]\n        entries.append(('routing_selection.json'")
s=s.replace("        entries += [('k_'+name, p) for name, p in ep.artifact_entries(root)]", "        try: entries += [('k_'+name, p) for name, p in ep.artifact_entries(root)]\n        except Exception as error: errors.append(dict(file='k',error=type(error).__name__))")
s=s.replace("    if mode=='r': timing.update(task_a=dict(status='UNAVAILABLE'), routing_types='UNAVAILABLE')", "    if mode=='r': timing.update(task_a=dict(status='UNAVAILABLE',task_iv=chain_value['status']),\n        chain=chain_value['status'], routing_types='UNAVAILABLE')")
s=s.replace("            timing['task_a'] = {k:timing['nsample'].get(k) for k in ('status','task_i','task_ii','task_iii')}", "            timing['task_a'] = {k:timing['nsample'].get(k) for k in ('status','task_i','task_ii','task_iii')}\n            timing['task_a']['task_iv'] = chain_value['status']\n            if chain_value['status'] != 'PASS': timing['task_a']['status'] = 'FAIL'")
s=s.replace("timing['task_a'] = dict(status='FAIL',reason='E96')", "timing['task_a'] = dict(status='FAIL',reason='E96',task_iv=chain_value['status'])")
# The fixed tail reservation is not an accounting result. Charge timings at its
# exact serialized size, both to aggregate and helper totals, after all metadata.
a=s.index("    if mode=='r':\n        try:\n            total = sum(p.stat().st_size")
b=s.index('    # Retain a local publication report',a)
s=s[:a]+'''    if mode=='r':
        try:
            account(target, timing)
        except Exception as error:
            timing['aggregate_limit_status'] = 'UNAVAILABLE'
'''+s[b:]
a=s.index('\ndef publish(')
s=s[:a]+'''
def account(target, timing):
    sizes = {str(p.relative_to(target)):p.stat().st_size for p in Path(target).rglob('*')
             if p.is_file() and p != Path(target)/'timings.json'}
    total = sum(sizes.values())
    helper = sum(size for name,size in sizes.items() if name != 'p_sample.json' and not name.startswith('rd0/'))
    timing.update(publication_bytes_before_timings=total, helper_limit_bytes=LIMIT,
        aggregate_publication_bytes=total, helper_publication_bytes=helper,
        aggregate_limit_status='PASS', helper_limit_status='PASS')
    while True:
        size = len((json.dumps(timing,sort_keys=True,indent=2)+'\\n').encode())
        new = dict(aggregate_publication_bytes=total+size, helper_publication_bytes=helper+size,
            aggregate_limit_status='PASS' if total+size < LIMIT else 'FAIL',
            helper_limit_status='PASS' if helper+size < LIMIT else 'FAIL')
        if all(timing[k] == v for k,v in new.items()):
            return
        timing.update(new)

'''+s[a:]
s=s.replace("        elif mode == 'check':", "        elif mode == 'chain':\n            import ch\n            ch.run(kit, root)\n        elif mode == 'check':")
replace(p,s)
