F=/scratch/jjyeung/orch_n30/fb_pack; kill -CONT 311364 $(pgrep -P 311364); ps -o pid,stat -p 311364 | tail -1
ls $F/camform/out | tr '\n' ' '; echo; tail -c 1500 $F/camform/dispatch.log; echo; head -c 5000 $F/camform/out/REPORT.md 2>/dev/null
