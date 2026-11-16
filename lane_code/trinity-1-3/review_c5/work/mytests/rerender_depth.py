import sys,json
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/review_c5/work/tests_r5']
from trace_format.contracts import contract_epoch
from fixtures_contracts import fixture, own_geometry
from student_pilot import carrier_c1_routing as C
def row(tok_style,pts):
    token='<depth_at frame=2 pts='+(json.dumps(pts,separators=(',',':')) if tok_style=='json' else '['+','.join(f'({a},{b})' for a,b in pts)+']')+'>'
    ev=dict(kind='tool_response',call_id='c1',name='depth_at',text='x',points=[dict(label=f'P{i+1}',requested_frame=2,actual_frame=2) for i in range(len(pts))])
    return dict(events=[dict(kind='plan',text='Read.'),dict(kind='tool_call',call_id='c1',name='depth_at',arguments={'frame':2,'pts':pts},token=token),ev],answer='<answer>x</answer>',trace_revision='3.14')
for kind in ('landscape','nadir_positive'):
  for style,pts in (('json',[[300,500]]),('paren',[[300,500]]),('json',[[10,500]]),('json',[[300,500],[400,500],[500,500],[600,500],[700,500]])):
    with contract_epoch(True):
        try:
            t,sp,_=C.rerender(row(style,pts),own_geometry(fixture(kind)[1]()))
            out=t[sp[0]['start']:sp[0]['end']].replace('\n',' | ')
        except Exception as e: out='EXC '+type(e).__name__+' '+str(e)[:120]
    print(kind,style,len(pts),pts[0],'->',out[:200])
