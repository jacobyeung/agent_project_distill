"""Production v3.14 row dispatcher. Room rows measure the floor footprint."""
from . import box_v313 as B, ground_v313 as G, ground_v312 as old
TYPES = (*old.TYPES, 'object_counting', 'object_appearance_order', 'object_size_estimation',
         'camera_obj_abs_dist', 'camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
         'room_size_estimation', 'relative_count', 'absolute_direction_object')
def render(item, session, token_count):
    typ=item['type']
    if typ=='room_size_estimation':
        from .room_rows_v314 import render as render_room
        row=render_room(item,session,token_count)
    elif typ in ('relative_count', 'absolute_direction_object', 'object_counting'):
        from .gaps_v314 import render as render_gap
        row=render_gap(item,session,token_count)
    elif typ.startswith('camera_obj_'):
        row=B.render_camera(item,session,token_count)
    elif typ in ('object_counting','object_appearance_order'):
        row=G.render(item,session,token_count)
    elif typ in ('object_abs_distance','object_rel_distance'):
        row=B.render(item,session,token_count)
    elif typ=='object_size_estimation':
        if not item.get('gt_authority'):raise old.RowRefusal('independent_gt_authority_missing')
        if session.events:raise ValueError('render requires a fresh session')
        name=old.valid_name(item['roles']['a'])
        call=f'<ground obj="{name}" mode="box">'
        body=session.execute(call)
        if session.box_registry.states.get(name)!='ok':raise old.RowRefusal('box_unavailable')
        records=[session.box_registry.records[l] for l in session.box_registry.bindings[name]]
        answer=str(round(100*max(max(r['value']['lengths']) for r in records)))
        if str(item['gt_answer'])!=answer:raise old.RowRefusal('independent_size_disagreement')
        text=f'<think>\n{call}\n{old.wrap(body)}\nThe longest box side is {answer} cm.\n</think>'
        suffix=text+f'\n<answer>{answer}</answer>'
        row=dict(qid=item['qid'],type=typ,question=item['question'],options=item.get('options',[]),
            answer=answer,answer_content=answer,suffix=suffix,suffix_tokens=token_count(suffix),events=list(session.events))
    else:row=old.render(item,session,token_count)
    if not 0<=row['suffix_tokens']<=5000:raise old.RowRefusal('suffix_cap')
    row.update(spec_version='3.14',trace_program_version='3.14',training_admitted=True)
    return row
