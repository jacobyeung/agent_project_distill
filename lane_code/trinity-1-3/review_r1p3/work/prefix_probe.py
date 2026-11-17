import sys,json,collections
sys.path[:0]=[sys.argv[1],sys.argv[1]+'/generator/derivgen_v7']
from student_pilot import carrier_c1_routing as routing
from student_pilot.loader_audit import row_metadata,draw_breakdown
events=[dict(kind='plan',text='Measure the distance between the objects.')]
target,spans=routing.render(events,'2')
rgb=dict(frames=[dict(path='x/'+str(i)+'.png',sha256='0'*64,source_index=i) for i in range(32)],fps=1,total_num_frames=32)
out=collections.Counter()
for ds in ('scannetpp','scannetppv2','scannet','arkitscenes'):
    for scene in ('0a5c013435','scene0000_00','41069025','abc/def'):
        row=dict(schema='derivgen-row-v2',form='spec-v3.8-calculator-v2',infrastructure_only=False,qid='q_'+ds+scene,
            question_type='absolute_distance_object',question='How far?',events=events,answer='2',gt_answer='2',target=target,
            tool_output_spans=spans,provenance=dict(canonical=ds+'/'+scene,frame_indices=list(range(32)),source_row_sha256='1'*64,physical_group='g'))
        staged=json.loads(json.dumps(routing.c1_row(row,rgb)))
        assert 'provenance' not in staged
        out[(ds,row_metadata(staged,'routing','absolute_distance')['prefix'])]+=1
print(dict(out))
def bd(n,unk):
    meta={'routing':{i:dict(family='absolute_distance',prefix='unknown' if i<unk else 'scannet/') for i in range(n)}}
    draws=collections.Counter({('routing',i):1 for i in range(n)})
    return draw_breakdown(meta,draws,routing_available=True)['routing_absolute_distance']['prefix_check']['status']
print({f'{u}/{n}':bd(n,u) for n,u in ((100,0),(100,1),(100,2),(1000,10),(1000,11),(0,0),(1,1))})
