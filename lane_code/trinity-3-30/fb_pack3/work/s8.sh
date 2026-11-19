cd /scratch/jjyeung/orch_n30/sb_own400/out/real400_score_n && sha256sum DISPLACEMENT_RESULT.json | cut -c1-16; /scratch/jjyeung/envs/p1cpu/bin/python -B -c "
import json;d=json.load(open('DISPLACEMENT_RESULT.json'));print('chosen',d['chosen_donor'],'captures',d['captures'],'pairs',d['pairs'])
dd=d['displacement']
for f in dd['folds']+[dict(name='combined',**dd['combined'])]:
  print(f['name'],{k:(round(v['mra'],4) if 'mra' in v else round(v['points'],5),[round(x,5) for x in v['ci95']],v['rooms']) for k,v in f.items() if k!='name'})
print('global',dd['global_fit_report_only'])"
