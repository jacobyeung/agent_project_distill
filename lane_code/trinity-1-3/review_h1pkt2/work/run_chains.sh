#!/bin/bash
cd /scratch/jjyeung/orch_n30/review_h1pkt2/work/h1c; export PYTHONDONTWRITEBYTECODE=1; P=/scratch/jjyeung/envs/p1cpu/bin/python
for c in signal fileonly full200; do timeout 900 $P -B rv/rv_run_chain2.py $c > /scratch/jjyeung/orch_n30/review_h1pkt2/work/log_chain_$c.txt 2>&1; echo "$c rc=$?" >> /scratch/jjyeung/orch_n30/review_h1pkt2/work/chains.done; done
timeout 900 $P -B rv/rv_run_chain_hfail2.py hfail > /scratch/jjyeung/orch_n30/review_h1pkt2/work/log_chain_hfail.txt 2>&1; echo "hfail rc=$?" >> /scratch/jjyeung/orch_n30/review_h1pkt2/work/chains.done
echo ALLDONE >> /scratch/jjyeung/orch_n30/review_h1pkt2/work/chains.done
