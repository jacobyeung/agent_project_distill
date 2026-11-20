import json,sys
from pathlib import Path
o=Path(sys.argv[1]); p=lambda x:'%.2f'%(100*x)
d=json.load(open(o/'SCORES.json'))
print('merged',d['meta'].get('completed'),'pairs',d['meta'].get('pairs'))
for k,v in sorted(d['cells'].items()): print('cell',k,p(v['answer']),'n',v['completed'],'/',v['expected'],'missing',len(v['missing']))
for k,v in sorted(d['reworded_minus_original'].items()): a=v['answer'];print('rew-orig',k,p(a['value']),'[%s,%s]'%(p(a['ci95'][0]),p(a['ci95'][1])),'n',a['n'],'rooms',a['rooms'])
for n in ('H400','H200'):
    f=o/('SCORES_vs_%s.json'%n)
    if not f.exists(): continue
    e=json.load(open(f))
    for k,v in sorted(e['current_minus_other'].items()):
        a=v['answer'] if 'answer' in v else v;print('544-%s'%n[1:],k,p(a['value']),'[%s,%s]'%(p(a['ci95'][0]),p(a['ci95'][1])),'n',a['n'])
for n in ('H400','H200'):
    f=o/('ALONE_%s.json'%n)
    if not f.exists(): continue
    e=json.load(open(f))
    for k,v in sorted(e['reworded_minus_original'].items()):
        a=v['answer'];b=d['reworded_minus_original'][k]['answer'];print('rew-orig@%s'%n[1:],k,p(a['value']),'gap change 544-%s'%n[1:],p(b['value']-a['value']))
