timeout 60 srun --jobid=170294 --overlap --ntasks=1 --cpus-per-task=1 --mem=1G --gres=none bash -c 'R=$(ls -d /tmp/a15_170294_*|head -1); python3 -c "
import json,sys;d=json.load(open(\"$R/run/p/PROOF.json\"))
print({k:v for k,v in d.items() if k not in (\"records\",\"geometry_check\")})
rec=d.get(\"records\",[]);print(\"records\",len(rec))
for r in rec[:10]: print({k:(v if len(str(v))<120 else str(v)[:120]) for k,v in r.items()} if isinstance(r,dict) else r)
"; ls $R/run/j0; for f in $R/run/j0/*; do echo $f; head -c 600 $f; echo; done; cat $R/run/PHASES.json | tail -8'
