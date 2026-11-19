W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf19; date -u +%TZ; tmux ls | grep tr11
wc -l $C/focused.log; tail -8 $C/focused.log; grep -c "ok$" $C/focused.log; grep -E "^Ran|FAILED|OK" $C/focused.log | tail; cat $C/core.log
python3 -c "import json;d=json.load(open('$C/pkg/work/build19/proofs/final_focused/TESTS.json'));print(d['tests'],d['failures'],d['errors'],d['successful'])"
tail -c 400 $W/work/rev19_dispatch.log
