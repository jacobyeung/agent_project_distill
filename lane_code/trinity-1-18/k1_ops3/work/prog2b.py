import json,time
rows=[json.loads(l) for l in open('/scratch/jjyeung/k1/run_tower_sam_2/PROGRESS.jsonl')]
t0=1794790565
c=[r for r in rows if r['event']=='capture_commit' and r['unix']>t0+40]
print(time.strftime('%H:%M:%SZ',time.gmtime()),'committed_total',len({r['canonical'] for r in rows if r['event']=='capture_commit'}),'resumed',len(c),'last',rows[-1]['event'],rows[-1].get('canonical'),'age_s',round(time.time()-rows[-1]['unix']))
if len(c)>1: print('mean_s_per_capture',round((c[-1]['unix']-c[0]['unix'])/(len(c)-1)))
print([r['event'] for r in rows if r['event'] in ('failed','complete')])
