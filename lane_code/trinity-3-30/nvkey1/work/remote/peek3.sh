K=/scratch/jjyeung/orch_n30/nvkey1/work
python3 -c "import json; d=json.load(open('$K/c0_caps.json')); print('CAPS', json.dumps(d['captures'])); print('GT', json.dumps(d['gt']))"
tail -3 $K/runner.log; cat $K/meter/METER.json; wc -l $K/out/10_bake32.jsonl
grep -c '"status": 200' $K/meter/CALLS.jsonl; grep -v '"status": 200' $K/meter/CALLS.jsonl | tail -3 | cut -c1-300
