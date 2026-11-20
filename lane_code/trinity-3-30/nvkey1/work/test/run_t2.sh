cd /scratch/jjyeung/orch_n30/nvkey1/work/test
mkdir -p tk2/queue tk2/ctl && echo 60 > tk2/ctl/RATE && echo 4 > tk2/ctl/INFLIGHT && cp tk/queue/10_t.jsonl tk2/queue/10_t.jsonl
/scratch/jjyeung/envs/p1cpu/bin/python fake_server.py 18778 > /dev/null 2>&1 & SP=$!
sleep 1
sed -e "s#URL = 'https://inference-api.nvidia.com/v1/chat/completions'#URL = 'http://127.0.0.1:18778/v1/chat/completions'#" -e "s#^EV = .*#EV = '/scratch/jjyeung/orch_n30/nvkey1/work/test/ev'#" -e "s#^ALLOC = .*#ALLOC = '/scratch/jjyeung/orch_n30/nvkey1/work/test/ALLOC.md'#" ../kit/nvrun.py > nvrun_test.py
NVK=/scratch/jjyeung/orch_n30/nvkey1/work/test/tk2 NV_INFERENCE_API_KEY=fake1 NV_INFERENCE_API_KEY2=fake2 NV_INFERENCE_API_KEY3=fake3 NV_INFERENCE_API_KEY4=fake4 timeout 150 /scratch/jjyeung/envs/p1cpu/bin/python nvrun_test.py 15; echo rc=$?
kill $SP
cat tk2/runner.log; wc -l tk2/meter/CALLS.jsonl; cut -c1-200 tk2/out/10_t.jsonl; cat tk2/faults/*.gaveup.jsonl; cat ev/METER.json
