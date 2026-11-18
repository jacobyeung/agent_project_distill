W=/project/community/jjyeung/okh7/e6fc152498; tail -n 3 $W/callcount.out | cut -c1-300; pgrep -u $USER -f callcount.py >/dev/null && echo RUNNING
TZ=UTC squeue -u $USER -h -o '%i %j %T %M %P' 
