set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $K
Q=$K/queue/20_c0census32.jsonl
[ -f $Q ] || { $P -B kit/c0_jobs.py $Q.tmp gcp/google/gemini-4-argon high && $P -B kit/c0_jobs.py $Q.tmp openai/openai/gpt-6.2-astra high && mv $Q.tmp $Q; }
REST=$($P -c "import json; m=json.load(open('$K/c1/C1_MANIFEST.json')); bo=set('ka9594e8caae,kc2430767aa3,kc88e2007abb,k01d89b248dc,kf54aa2cf5b1,k03c5a6666c8,kc57e8edfa5c,k234381f08ec'.split(',')); print(','.join(a for a in m if a not in bo))")
Q2=$K/queue/30_c1rest32.jsonl
[ -f $Q2 ] || { $P -B kit/c1_jobs.py $Q2.tmp gcp/google/gemini-4-argon high 32 $REST && $P -B kit/c1_jobs.py $Q2.tmp openai/openai/gpt-6.2-astra high 32 $REST && mv $Q2.tmp $Q2; }
Q3=$K/queue/31_c1all64.jsonl
[ -f $Q3 ] || { $P -B kit/c1_jobs.py $Q3.tmp gcp/google/gemini-4-argon high 64 all && $P -B kit/c1_jobs.py $Q3.tmp openai/openai/gpt-6.2-astra high 64 all && mv $Q3.tmp $Q3; }
wc -l $K/queue/*.jsonl; echo 200 > $K/ctl/BUDGET; cat $K/ctl/RATE
grep 'gpt-6.2-astra' $K/meter/CALLS.jsonl | tail -3 | cut -c1-420
tail -3 $K/runner.log
