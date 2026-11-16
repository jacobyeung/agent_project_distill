"""F3 refute: VSI-Bench harness shards partition scenes, charge only their own scenes, fit 21,600 s with 600 s reserve."""
import sys
from pathlib import Path
N=Path('/scratch/jjyeung/orch_n30/b07_offread/builds/N');sys.path.insert(0,str(N))
from offnative import paths
from offnative.shards import plan,cost,LIMIT,RESERVE,DEFAULT_BUDGETS
from offnative.cohort import cohort
from offkit.report import key

def test_F3_scene_partition_and_honest_estimate():
    items=cohort('vsibench5130');p=plan(items);by={key(r):r for r in items}
    assert LIMIT==21600 and RESERVE==600 and p['partition_unit']=='scene'
    seen={};all_ids=[]
    for s in p['shards']:
        rows=[by[k] for k in s['ids']];all_ids+=s['ids']
        scenes={(r['dataset'],r['scene_name']) for r in rows}
        assert scenes=={tuple(x) for x in s['scenes']} and len(scenes)==s['scene_count']
        for sc in scenes:assert sc not in seen,(sc,seen.get(sc),s['index']);seen[sc]=s['index']
        per_scene=sum(DEFAULT_BUDGETS[n] for n in DEFAULT_BUDGETS if n.startswith('scene_'))
        fixed=sum(v for n,v in DEFAULT_BUDGETS.items() if not n.startswith('scene_'))
        honest=1.25*(sum(cost(r) for r in rows)+per_scene*len(scenes)+fixed)+RESERVE
        assert abs(s['estimated_seconds']-honest)<1e-6,(s['index'],s['estimated_seconds'],honest)
        assert s['estimated_seconds']<=LIMIT,(s['index'],s['estimated_seconds'])
        # the reviewer-2 honest floor (decode + G3T per own scene) is also met
        assert s['estimated_seconds']>=1.25*(sum(cost(r) for r in rows)+3.8*len(scenes))
    assert sorted(all_ids)==sorted(by) and len(all_ids)==len(set(all_ids))
    assert len(seen)==len({(r['dataset'],r['scene_name']) for r in items})==288
    print(p['count'],max(s['estimated_seconds'] for s in p['shards']),min(s['estimated_seconds'] for s in p['shards']))
