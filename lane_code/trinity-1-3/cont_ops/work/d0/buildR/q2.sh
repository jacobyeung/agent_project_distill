B=/scratch/jjyeung/orch_n30/b07_offread/builds/R; K=/scratch/jjyeung/orch_n30/b07_offread/kit/offkit
grep -n "d0_ended\|stopped_under_rule\|no_further_allocation\|completed_step_1000" $B/kit/rebind.py $K/*.py | head -30
echo "#### fetch/report"; grep -n "def fetch\|def report\|def cmd_\|COMPLETE.json\|SPEC.json\|request.json\|packet\|unpack" $B/kit/rebind.py | head -60
echo "#### tests mention d0_ended"; grep -ln "d0_ended" $B/tests/*.py
ls $B/work | head -40
