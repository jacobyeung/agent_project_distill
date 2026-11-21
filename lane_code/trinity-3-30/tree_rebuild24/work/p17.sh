W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/work/e3t_900003; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;r=json.load(open('E3.json'))
for x in r['receipts']: print(x['name'],x['bytes'],x['sha256'],x['md5'],x['generation'])"
