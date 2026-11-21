date -u +%TZ
cd /tmp && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/n_review/r1i/s94.py < /dev/null 2>&1 | cut -c1-300
