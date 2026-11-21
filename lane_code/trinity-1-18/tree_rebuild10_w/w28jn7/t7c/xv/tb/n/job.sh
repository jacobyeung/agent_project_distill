#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
python3 -c "import sys;f=open(sys.argv[1],\"w\");f.write(\"FIRST_RECORD https://storage.example/upload?id=abc\\n\");f.write(\"x\"*300000+\"\\n\");f.write(\"LAST_RECORD http://h/s\\n\")" "$N/tb.txt"; exit 1
