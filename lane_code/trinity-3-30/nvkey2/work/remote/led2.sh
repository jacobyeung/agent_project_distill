K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; wc -l out/4*.jsonl out/56*.jsonl; tail -2 runner.log; cat meter/METER.json
$P -B kit/ledger.py nvkey2 '{"55_v2cal": "V2 alias namer calibration: 300 random K1-train GT instance crops, 30 per call (tag calibration); failed its control bar", "56_v2o4": "V2 alias candidates (uncertified namer; candidates only): 146 O4 instances from the phrase-kit no-proposal records, Argon and Astra"}'
