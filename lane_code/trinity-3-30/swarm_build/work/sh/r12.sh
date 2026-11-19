R=/scratch/jjyeung/orch_n30
sed -n 1,45p $R/sb_records/out/RECORDS_REPORT.md
cat $R/sb_queue/queue.txt | tr "\n" " "
