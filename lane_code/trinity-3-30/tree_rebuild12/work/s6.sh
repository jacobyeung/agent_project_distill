W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21/pkg; B=$W/w21/work/build21
ls $C/work/build21/ | grep -E 'run.sh|test21.py|edge_test16|stage_test16|export_edges17|export_mutation17' ; ls $C/work | head
M="tests.test_r1_build20 tests.test_r1_build19 tests.test_r1_build18 tests.test_r1_build17 tests.test_r1_export17 tests.test_r1_build16 tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset export_mutation17.HashTwin.test_same_size_shard_refuses"
cat > $W/work/conf21/ff.sh <<EOS
cd $C && mkdir -p work/tmp
B21_PROOF=final_focused nice -n 10 bash work/build21/run.sh work/build21/test21.py $M > $W/work/conf21/ff_focused.log 2>&1; echo focused \$? >> $W/work/conf21/ff_rc
B21_PROOF=edges nice -n 10 bash work/build21/run.sh work/build21/test21.py edge_test16.Edges stage_test16.Staging > $W/work/conf21/ff_edges.log 2>&1; echo edges \$? >> $W/work/conf21/ff_rc
B21_PROOF=producer_edges nice -n 10 bash work/build21/run.sh work/build21/test21.py export_edges17.ProducerEdges > $W/work/conf21/ff_pedges.log 2>&1; echo pedges \$? >> $W/work/conf21/ff_rc
EOS
tmux new -d -s tr12_ff "bash $W/work/conf21/ff.sh"
python3 - <<'PY'
import json
f=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/build21/proofs/capacity/400/q/f.json'))
def show(x,d=0):
    if isinstance(x,dict):
        for k,v in list(x.items())[:25]:
            if isinstance(v,(dict,list)): print(' '*d+str(k)+':'); show(v,d+2)
            else: print(' '*d+f'{k}: {str(v)[:150]}')
    elif isinstance(x,list):
        print(' '*d+f'[list len {len(x)}]'); 
        if x: show(x[0],d+2)
show(f)
PY
sleep 20; tail -3 $W/work/review21_dispatch.log; cat $W/work/conf21/ff_rc 2>/dev/null
