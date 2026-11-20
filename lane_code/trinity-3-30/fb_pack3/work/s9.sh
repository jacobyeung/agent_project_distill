cd /scratch/jjyeung/orch_n30/sb_own400/out && tail -3 real400_score_n.log; cd real400_score_n && ls; [ -f SCORE_RESULT.json ] && sha256sum SCORE_RESULT.json DISTANCE_ROWS.json DISPLACEMENT_RESULT.json BARS_FROZEN.json | cut -c1-16,65- && /scratch/jjyeung/envs/p1cpu/bin/python -B -c "
import json;d=json.load(open('SCORE_RESULT.json'));r=d['routed_distance']
for f in r['folds']+[dict(name='combined',**r['combined'])]:
  print(f['name'],{k:(round(v['mra'],3) if 'mra' in v else round(v['points'],3),[round(x,3) for x in v['ci95']],v['rooms']) for k,v in f.items() if k!='name'})
print('harm',r['chosen_donor_harm'],r['guard_action'],'missing',len(d['missing']),d['missing'][:3],'secs',round(d['seconds']))
rows=json.load(open('DISTANCE_ROWS.json'))['rows'];print('distance rows',len(rows),'refusals',sum(1 for x in rows if x['refusal']))"
