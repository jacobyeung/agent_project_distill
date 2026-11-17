python3 - /project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub_b01ec87a6f29b00029a87/curve.json <<'PY'
import json,sys
c=json.load(open(sys.argv[1]))['per_type']
f=lambda d:f"{d['value']:.3f} [{d['ci95'][0]:.3f},{d['ci95'][1]:.3f}]" if d and d.get('ci95') else (f"{d['value']}" if d else '-')
for t,a in c.items():
    for mode,v in a['own'].items():
        m1,m2,m3=v['M1'],v['M2'],v['M3']
        head={k:f(m2[k]) for k in ('absolute_error_m','error_deg','correct','direction_accuracy','relative_error') if k in m2}
        print(t,mode,'n',v['n'],'| M1 call',f(m1['call_rate']),'exact',f(m1['exact']),'abf',m1['answer_before_first_call']['value'],'pass',m1['passes_bars'],
              '| M2 task',f(m2['task_accuracy']),head,'unserved',m2['unserved_rate']['value'],'err',m2['error_rate']['value'],
              '| M3 elig',m3.get('eligible'),'follow',f(m3.get('follow')),'stick',f(m3.get('stick')),'other',f(m3.get('other')),'pass',m3.get('passes_bars'))
PY
