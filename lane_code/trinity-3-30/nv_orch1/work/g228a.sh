K=/scratch/jjyeung/orch_n30/nvkey1/work; G=/scratch/jjyeung/orch_n30/grd_funnel1/work
ls -la $K/c0/C0_MANIFEST.json $G/items544.jsonl $G/objects544.jsonl $K/out/20_c0census32.jsonl $K/scores/C0_census32.json 1>&2
du -sh $K/c0 1>&2
tar czf - -C / ${K#/}/c0/C0_MANIFEST.json ${G#/}/items544.jsonl ${G#/}/objects544.jsonl ${K#/}/out/20_c0census32.jsonl ${K#/}/scores/C0_census32.json
