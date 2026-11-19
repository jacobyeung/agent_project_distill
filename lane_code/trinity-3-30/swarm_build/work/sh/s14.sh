R=/scratch/jjyeung/orch_n30; ls $R/sb_scale2/out | tr "\n" " "; echo; cat $R/sb_scale2/STATUS.md | cut -c1-900; tail -5 $R/sb_scale2/out/completion.log | cut -c1-300; ls -la $R/sb_scale2/out/geometry | tail -5
ps -eo pid,etime,pcpu,rss,args | grep -v grep | grep sb_scale2 | cut -c1-200 | head
