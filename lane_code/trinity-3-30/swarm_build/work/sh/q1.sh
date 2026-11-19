set -u
R=/scratch/jjyeung/orch_n30
printf "sb_framepool\nsb_rspecrev\nsb_rowF\nsb_rowOI\n" > $R/sb_queue/queue.txt
cat $R/sb_queue/queue.txt
