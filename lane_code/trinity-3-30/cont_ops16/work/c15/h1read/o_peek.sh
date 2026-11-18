export TZ=UTC
timeout 90 srun --overlap --jobid 170928 -n1 --cpus-per-task=1 --mem=2G bash -c 'G=/tmp/a_170928_aed15a8b7cb/sj/aaed15a8b7cb/r/a7/a0/results/0/g0.jsonl; wc -l $G; python3 - $G <<"PY"
import json,sys,collections
L=open(sys.argv[1]).read().split("\n")
rows=[json.loads(l) for l in L if l.strip().startswith("{")]
print("keys",sorted(rows[0].keys())[:40])
print({k:str(v)[:60] for k,v in rows[-1].items() if k not in ("token_ids","prompt_text","raw_generation","token_text")})
PY' 2>&1 | tail -20
