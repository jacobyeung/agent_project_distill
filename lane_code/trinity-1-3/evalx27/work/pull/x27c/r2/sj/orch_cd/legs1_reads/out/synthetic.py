"""Retained normalized synthetic journals that exercise every registered decision."""
import argparse,copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import decision as D
from test_reads import simple_rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);a=p.parse_args()
    root=local(a.dest);root.mkdir(parents=True,exist_ok=False);results={}
    cases=['m100_primary_reversal','m100_route_reversal','R3_caps','R3_dev858','R1_score','R1_calls',
           'R1_call_error','R1_version_error','R1b_path','R1b_score','R2_positive','R2_negative','R2_spans_zero','m200_persistent_R1']
    for name in cases:
        folder=root/name;folder.mkdir()
        if name.startswith(('m100_','R3_')):
            leg=simple_rows();parent=simple_rows();f17=simple_rows();dev=(simple_rows(),simple_rows())
            if name=='m100_primary_reversal':
                for r in leg:r['scores']=dict(answer=0,released_answer=0)
            if name=='m100_route_reversal':
                for values,score in ((leg,0),(parent,1),(f17,1)):
                    route=simple_rows(score,typ='route_planning',stratum='missing_released')
                    for r in route:r['key']='route'+r['key'];r['scores']['released_answer']=None
                    values.extend(route)
            if name=='R3_caps':leg[0]['capped']=leg[1]['capped']=True
            if name=='R3_dev858':dev=(simple_rows(0,n=858),simple_rows(1,n=858))
            journals=dict(leg=leg,parent=parent,f17=f17,dev858_leg=dev[0],dev858_f17=dev[1])
            for arm,rs in journals.items():(folder/(arm+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rs))
            result=D.direct_rules(rows(folder/'leg.jsonl'),rows(folder/'parent.jsonl'),rows(folder/'f17.jsonl'),
                (rows(folder/'dev858_leg.jsonl'),rows(folder/'dev858_f17.jsonl')))
            key='m100_reversal' if name.startswith('m100_') else 'R3';expected='STOP' if key=='m100_reversal' else 'FAIL'
        else:
            arms={k:simple_rows() for k in ('forced_route','scripted','forced_direct','unflagged')}
            for r in arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=0;r['called']=False
            if name=='R1_score':
                for r in arms['forced_route']:r['scores']['released_answer']=r['scores']['answer']=.9
            if name=='R1_calls':
                for r in arms['forced_route'][:6]:r['called']=False
            if name in ('R1_call_error','m200_persistent_R1'):arms['forced_route'][0]['call_errors']=1
            if name=='R1_version_error':arms['forced_route'][0]['version_errors']=1
            if name=='R1b_path':
                for r in arms['unflagged'][:6]:r['called']=False
            if name=='R1b_score':
                for r in arms['unflagged']:r['scores']['released_answer']=r['scores']['answer']=.97
            if name=='R2_negative':
                for r in arms['forced_route']:r['scores']['released_answer']=r['scores']['answer']=0
                for r in arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=1
            if name=='R2_spans_zero':
                for r in arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=1
            for arm,rs in arms.items():(folder/(arm+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rs))
            result=D.routed_rules({k:rows(folder/(k+'.jsonl')) for k in arms},{'object_abs_distance':'route'},
                raised=['object_abs_distance'] if name=='m200_persistent_R1' else [],step=200 if name=='m200_persistent_R1' else 100)
            result=result['per_type']['object_abs_distance']
            key='R1b' if name.startswith('R1b') else 'R2' if name.startswith('R2') else 'R1'
            expected='PASS' if name=='R2_positive' else 'INCONCLUSIVE' if name=='R2_spans_zero' else 'STOP' if name=='m200_persistent_R1' else 'FAIL'
        if not result[key].startswith(expected):raise AssertionError((name,result[key],expected))
        dump(folder/'REPORT.json',dict(synthetic=True,result=result))
        results[name]=dict(verdict=result[key],expected=expected,pass_=True,journals={p.name:pin(p) for p in sorted(folder.glob('*.jsonl'))})
    dump(root/'RESULTS.json',dict(synthetic=True,cases=len(cases),passed=len(results),results=results))
    print(f'PASS: {len(results)} retained synthetic journal scenarios')
if __name__=='__main__':main()
