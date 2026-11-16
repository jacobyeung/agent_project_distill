G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u; free -g | head -2
ps -u jjyeung -o pid,rss,pcpu,etime,cmd | grep k1_infer | grep -v grep | cut -c1-160
tail -3 logs/kit_tests2.log; tail -c 300 logs/cpu_da3.log; echo; tail -c 300 logs/cpu_mapanything.log; ls harness/out_ref/captures | wc -l
