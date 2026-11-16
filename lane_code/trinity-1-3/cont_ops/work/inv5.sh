export TZ=UTC
cd /home/jjyeung/okit && env -u TK_JOB_START sbatch --test-only -J a15_cot_ap0b0c99e1 -o /dev/null -e /home/jjyeung/okit/x/07ca49df/o/%j.err /home/jjyeung/okit/j/07ca49df.sh 2>&1
df -PB1 /project/community | tail -1
date -u +%FT%TZ
