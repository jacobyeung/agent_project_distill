import json,sys
L='/scratch/jjyeung/orch_n30/tree_rebuild_w';P='/scratch/jjyeung/orch_n30/review_tree9/pkg'
def outcomes(d):
    o={}
    for t in d['passed']:o[t]='pass'
    for t,_ in d['failures']:o[t]='fail'
    for t,_ in d['errors']:o[t]='error'
    for t,_ in d['skips']:o[t]='skip'
    return o
b=outcomes(json.load(open(L+'/work/build9/proofs/suite_tree/results.json')))
summary={}
for g in ('r2','generator','legacy_sel'):
    d=json.load(open(P+'/work/rv_suite/'+g+'/results.json'));m=outcomes(d)
    diff={t:(m[t],b.get(t,'absent')) for t in m if m[t]!=b.get(t)}
    summary[g]=dict(tests=d['tests'],passed=len(d['passed']),failures=len(d['failures']),errors=len(d['errors']),skips=len(d['skips']),complete=d['complete'],same=sum(m[t]==b.get(t) for t in m),differ=diff)
    print(g,{k:v for k,v in summary[g].items() if k!='differ'},'differ:',json.dumps(diff)[:1500])
json.dump(summary,open('/scratch/jjyeung/orch_n30/review_tree9/proofs/SUITE_RERUN.json','w'),indent=1)
