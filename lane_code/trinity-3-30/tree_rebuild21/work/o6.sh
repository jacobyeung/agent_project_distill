export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173725; L=$X/j/$J.log
grep -n "E96\|E98\|nsample\|routing_types\|task_a\|Traceback\|most recent\|Error:\|ValueError\|budget\|live" $L | grep -v '^[0-9]*:{"source\|^[0-9]*:{"remove_list\|^[0-9]*:{"pool' | cut -c1-500 | tail -40
ls $X/c_291c6f58/rcj; grep -n "E96\|E98" $X/c_291c6f58/rcj/*.py | cut -c1-250 | head -20
