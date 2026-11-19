R=/scratch/jjyeung/k1/own_170235
ls $R/metadata $R/logs; cat $R/metadata/budget.json; echo; head -c 1500 $R/metadata/admission.json; echo
python3 -c "
import json;t=json.load(open('$R/native/probe/TOKENS.json'));v=[x['seconds'] for x in t.values()];print(len(v),min(v),sum(v)/len(v),max(v));print(list(t.items())[:2])" 2>&1
ls $R/native/probe | head -3; head -c 600 $R/native/probe/PROGRESS.jsonl; echo; tail -c 400 $R/native/probe/PROGRESS.jsonl; echo
head -c 1500 $R/logs/a.log; echo; grep -c . $R/logs/a.log
