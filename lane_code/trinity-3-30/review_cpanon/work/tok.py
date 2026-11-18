import json,re,collections
E='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon7/ANON_SCAN_R1C4.json'
d=json.load(open(E))
c4=collections.Counter(t for h in d['hits'] for t in re.findall(r'(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])',h['text']))
s=open('/scratch/jjyeung/orch_n30/r1_ops6/work/xfer/scan1.out').read()
cp=collections.Counter(re.findall(r'(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])',s))
print('C4 only',[(t,n) for t,n in c4.items() if t not in cp])
print('Cp top',cp.most_common(15))
