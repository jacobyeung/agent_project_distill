from pathlib import Path
p=Path('code/engine.py');s=p.read_text().replace("limit=21600,boundary=None):", "limit=21600,boundary=None,deadline_utc=None,resume=(),proof_path=None):")
s=s.replace("    written=[];canary=[];cache={};reason='complete'",'''    from budget import Budget
    budget=Budget(deadline_utc);prior=None;prior_keys=[];canary=[]
    if resume:
        prior=merge(bound_path,resume,out/'PRIOR.json',partial=True)
        if prior['request_binding']!=request['binding']:raise ValueError('resume request/config/geometry/frame pins differ')
        prior_keys=[r['key'] for r in prior['items'] if r['arm']=='native']
        for r in prior['items']:
            if r['arm']=='native':budget.observe(r['question_type'],r['seconds'])
            if r['key'] in bound['canary']:canary.append(r)
        if set(bound['canary'])<=set(prior_keys) and not canary_check(canary,bound['canary'],request)['pass_']:
            raise ValueError('resume canary failed')
    proof_pin=None
    if proof_path:
        proof_value=load(proof_path);proof_value['read_binding']=request['binding'];dump(out/'PROOF.json',proof_value)
        proof_pin=pin(out/'PROOF.json')
    elif prior:proof_pin=prior.get('proof')
    written=[];cache={};reason='complete' ''')
s=s.replace("geometry_seconds=g.get('read_preparation_seconds',0))", "geometry_seconds=g.get('read_preparation_seconds',0),resume_keys=prior_keys,proof=proof_pin,budget=budget.record())")
s=s.replace("missing=[q for q in assigned if q not in written]", "missing=[q for q in assigned if q not in written and q not in prior_keys]")
s=s.replace("    for key in assigned:\n        if time.monotonic()", "    for key in assigned:\n        if key in prior_keys:continue\n        if not budget.allows(tasks[key]['question_type']):reason='deadline';break\n        if time.monotonic()")
s=s.replace("        written.append(key)","        budget.observe(task['question_type'],time.monotonic()-begin)\n        written.append(key)")
s=s.replace("if k==0 and written==bound['canary']:","if k==0 and key in bound['canary'] and set(bound['canary'])<=set(written+prior_keys):")
s=s.replace("receipt['projected_remaining_seconds']=sum(rates['camera' if t['question_type'] in CAMERA else 'other'] or 0 for t in remaining)","receipt['projected_remaining_seconds']=sum(budget.projected(t['question_type']) for t in remaining)\n            receipt['projection_rule']=budget.record()")
s=s.replace("bound=validate_bound(bound_path);seen=set();data=[];identity=None;completions=[]", "bound=validate_bound(bound_path);seen=set();data=[];identity=None;completions=[];proof_pin=None")
s=s.replace("        checked(r['geometry'])", "        checked(r['geometry'])\n        if c.get('proof'):\n            checked(c['proof'])\n            if proof_pin and proof_pin['sha256']!=c['proof']['sha256']:raise ValueError('proof pins differ')\n            proof_pin=c['proof']")
s=s.replace("        if c['reason']!='complete' and not partial:raise ValueError('shard did not complete')", "        if c['reason'] not in ('complete','deadline','time_limit') and not partial:raise ValueError('shard did not complete')")
s=s.replace("        if c['assigned']!=shard_keys", "        if not set(c.get('resume_keys',[]))<=seen:raise ValueError('resume history is absent or out of order')\n        if c['assigned']!=shard_keys")
s=s.replace("complete=not missing and all(c['reason']=='complete' for c in completions)","complete=not missing and all(c['reason'] in ('complete','deadline','time_limit') for c in completions),proof=proof_pin")
p.write_text(s)
p=Path('code/entry.py');s=p.read_text().replace("q.add_argument('--canary-only',", "q.add_argument('--deadline-utc');q.add_argument('--resume',nargs='*',default=[]);q.add_argument('--proof-result')\n            q.add_argument('--canary-only',")
s=s.replace('a.limit,boundary)','a.limit,boundary,a.deadline_utc,a.resume,a.proof_result)').replace('remaining,boundary)','remaining,boundary,a.deadline_utc,a.resume,a.proof_result)');p.write_text(s)
