cd /scratch/jjyeung/orch_n30/b10_reserve; export OMP_NUM_THREADS=4
while read s; do
  sp=$(python3 -c "import json,sys;r=json.load(open('out/R0_SCENES.json'));print(r['captures']['scannetpp/'+sys.argv[1]]['r0_split'])" $s)
  m=1; [ "$sp" = "R0-rl" ] && m=3
  echo "$s $sp $(nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -W ignore code/gen_questions.py data_cache/scannetpp/$s $sp $m out/questions/$s.jsonl.part 2>&1 | tail -1 | cut -c1-300)" >> work/gen_retry.log
  [ -s out/questions/$s.jsonl.part ] && mv out/questions/$s.jsonl.part out/questions/$s.jsonl
done < work/gen_retry.list
echo RETRY_DONE >> work/gen_retry.log
