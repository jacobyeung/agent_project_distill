#!/bin/bash
W=/scratch/jjyeung/orch_n30/aws_fetch/work
D=/lab_data/tarrlab/jacoby/agent_project/aws_evac/d/w19/evid/orchard_cr
/usr/bin/python3 -s $W/relay_reader.py \
 | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 \
 | timeout 14400 ssh -o ConnectTimeout=20 -o BatchMode=yes mind.cs.cmu.edu "srun -p cpu -c 1 --mem=2G -t 4:00:00 -J q7c2r bash -c 'mkdir -p $D && cat > $D/rt_b8b60bcef027.tar.part'"
echo "pipeline exit ${PIPESTATUS[*]}" 
