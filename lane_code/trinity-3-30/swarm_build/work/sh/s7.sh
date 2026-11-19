R=/scratch/jjyeung/orch_n30; echo "sb_scale1:sb_scale1" >> $R/sb_queue/queue.txt; tail -3 $R/sb_queue/queue.txt; ls $R/sb_queue/
sleep 75; tail -3 $R/sb_queue/*.log | tail -4; tail -4 $R/sb_cachk/work/price_s5.log
