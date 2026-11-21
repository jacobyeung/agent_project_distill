W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/work/e3t_900003; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;r=json.load(open('E3.json'))
print('checks',json.dumps(r.get('checks')))
print({k:(v if not isinstance(v,(list,dict)) else '...') for k,v in r.items()})
print('rate',json.dumps(r.get('rate'))[:600])
for x in r.get('objects',r.get('receipts',[])): print('REC',x['name'],x['bytes'],x['sha256'],x['md5'],x['generation'])"
grep -c . $W/work/e3t_900003/logs/*.jsonl 2>/dev/null; ls $W/work/e3t_900003/logs
