"""Production per-row entry points over fixed CPU GT masks and camera geometry."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from fixtures_contracts import fixture, masks

def generate(tree,kind='landscape'):
    sys.path[:0]=[str(Path(tree)/'generator/derivgen_v7'),str(Path(tree)/'generator/ground_rows_out')]
    import render_full as F
    import render_gaps_v314 as gaps
    from derivgen import ground_v313_distance as D
    from derivgen.programs_v314 import render
    from student_pilot import ground_lifting as backend
    geo=fixture(kind)[1]()
    geo.ids=np.array([1,2]);geo.labels=['chair','table']
    geo.inst=np.zeros((32,24,32),int)
    for iid,name in zip(geo.ids,geo.labels):geo.inst[masks(name).masks]=iid
    clip=NS(geo=geo,masks=lambda name:(masks(name).masks,np.ones(32)),
        programs=NS(T=NS(match_labels=lambda name,labels:[l for l in labels if l==name])))
    provider=gaps.instance_provider(clip)
    assert isinstance(provider,gaps.I.GTInstances)
    s=gaps.session(backend,clip,'object_counting')
    count=render(dict(qid='generator-count',type='object_counting',roles=dict(obj='chair'),question='How many chairs?',
        options=[],gt_answer='1',gt_authority='synthetic'),s,lambda text:len(text.split()))
    def fresh():
        return D.make_session(backend,clip,[],F.B.FusedBoxProvider(),multi_instance=True)
    probe=fresh()
    for n in ('chair','table'):probe.execute(f'<ground obj="{n}" mode="box">')
    gap='<gap a="chair" b="table" rule="box_grid_5cm">'
    distance=probe.execute(gap)
    item=dict(qid='generator-distance',type='object_abs_distance',roles=dict(a='chair',b='table'),
        question='How far is the chair from the table?',options=[],gt_answer=distance.split()[1],
        gt_authority='synthetic',target_distance_rule=F.B.RULE_GRID)
    row=F.B.render(item,fresh(),lambda text:len(text.split()))
    assert not row['not_seen'] and row['events'][-1]['call']==gap
    # Serialize the actual model-visible program, not private audit arrays.
    return dict(count=count['suffix'],distance=row['suffix'],count_events=count['events'],distance_events=row['events'])
