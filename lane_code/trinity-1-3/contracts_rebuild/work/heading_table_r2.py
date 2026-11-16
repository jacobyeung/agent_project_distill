from pathlib import Path
import json
L=Path(__file__).resolve().parents[1];S=L/'work/src_r2';B=L/'work/base/work/base/tree_b01ce449';T=L/'work/trees/r2_proof/base'
rows=[]
def add(call,fields,needs,why,rel,needle,behavior,test):
    p=S/rel if (S/rel).exists() else B/rel
    line=next(i for i,s in enumerate(p.read_text().splitlines(),1) if needle in s)
    for field in fields:
        rows.append([call,field,needs,why,f'[{rel}:{line}]({T/rel}:{line})',behavior,test])
head='student_pilot/carrier_c1_routing.py';calc='trace_format/calculator.py';ground='student_pilot/ground_lifting.py';session='trace_format/ground_v313.py';box='trace_format/box_v313.py'
parity='test_all_ground_fields_match_defined_computation';heads='test_all_relative_head_pairs';scope='test_frame_dependencies_and_world_rotation';calculator='test_calculator_field_scope_and_shared_implementation'
add('depth_at',['P label','camera frame','camera x','camera y','camera depth z','spread'],'no','R_i^T(P-t_i) and depth quantiles do not use reference yaw.',calc,'public_f1 =','Serve unchanged.',heads)
add('depth_at',['f1 horizontal x','f1 horizontal z'],'yes','Horizontal components use the reference level axes.',calc,'public_f1 =','Replace each component with heading unavailable.',heads)
add('depth_at',['f1 vertical y'],'no','up dot (P-t_1) is invariant under rotation about up.',calc,'public_f1 =','Serve unchanged inside the partial vector.',heads)
add('pose',['f1 centre x','f1 centre z'],'yes','Reference-level horizontal coordinates rotate with the reference yaw.',head,'def pose_text','Withhold component only.',heads)
add('pose',['f1 centre y'],'no','up dot (t_k-t_1) is independent of reference yaw.',head,'def pose_text','Serve unchanged.',heads)
add('pose',['yaw'],'yes','Angle from reference heading to frame k heading uses both headings.',head,'def pose_text','Withhold for undefined reference or queried frame; name the queried frame when it is degenerate.',scope)
add('move i to j',['dx','dz'],'no','L_i^T(t_j-t_i) cancels any common world rotation; only source i supplies level heading.',head,'def move_text','Serve unchanged if i has heading; otherwise withhold these components and name i.',heads+'; '+scope)
add('move i to j',['dy'],'no','up dot (t_j-t_i) needs neither endpoint heading.',head,'def move_text','Serve even if i or j is degenerate.',scope)
add('move i to j',['distance'],'no','Euclidean norm of t_j-t_i is rotation invariant.',head,'def move_text','Serve even if either endpoint is degenerate.',heads+'; '+scope)
add('turn i to j',['signed turn'],'no','atan2 of cross and dot between horizontal camera forward vectors uses headings i and j.',head,'def turn_text','Serve unchanged if both endpoint headings exist; otherwise name exactly the missing endpoints.',heads+'; '+scope)
add('ground head fallback',['name','ranked frame IDs','canvas u','canvas v','presence probability'],'no','Image coordinates and confidence are independent of any world basis.','student_pilot/carrier_c1_decode.py','def ground_text','Serve unchanged.',parity)
for call in ('ground centre','ground instances','gap witness','surface_pair','extent_ends'):
    loc=ground if call=='ground centre' else session
    needle='def render_ground' if call=='ground centre' else 'def point_line'
    add(call,['name','P label','camera frame','camera x','camera y','camera z'],'no','Camera-frame coordinates are R_i^T(P-t_i).',loc,needle,'Serve unchanged.',parity)
    add(call,['f1 horizontal x','f1 horizontal z'],'yes','Reference-level horizontal coordinates rotate with reference yaw.',loc,needle,'Withhold each horizontal component only.',parity)
    add(call,['f1 vertical y'],'no','up dot (P-t_1) is invariant.',loc,needle,'Serve unchanged.',parity)
add('ground centre',['support frames','best frame','spread','size length','size width','size height'],'no','Mask support, depth spread and physical box extents need no reference yaw.',ground,'def render_ground','Serve unchanged.',parity)
add('ground instances',['found count','instance ordinal','first frame'],'no','Enumeration and first supporting frame are image membership facts.',session,'body = f\'{name}: {len(entries)} found\'','Serve unchanged, including each partial point line.',parity)
add('ground box',['name','instance count','B label','support frames','best frame','size length','size width','size height'],'no','Support and physical extents do not require the reference heading.',box,'def ground(session,name)','Serve unchanged; private boxes still feed measurements.',parity)
add('ground box',['f1 centre x','f1 centre z','yaw'],'yes','Horizontal centre components and axis yaw use the reference basis.',box,'def ground(session,name)','Withhold each field only.',parity)
add('ground box',['f1 centre y'],'no','Vertical position is up dot (centre-t_1).',box,'def ground(session,name)','Serve unchanged.',parity)
for call,rel,needle in [('gap mask',session,'def _gap'),('gap box',box,'def measure'),('gap camera',box,'def cam_gap_body')]:
    add(call,['distance','candidate names','candidate distances','minimum names including ties','minimum distance'],'no','Minimum Euclidean distance between the same points is invariant under a common rigid rotation.',rel,needle,'Serve unchanged; witness camera coordinates remain available when enabled.',parity+'; test_relative_gap_fields_and_ties; test_actual_cpu_session')
add('gap witness',['role nearest point'],'no','The role names a selected point, not a world direction.',session,'def _gap','Serve unchanged.',parity)
add('surface_pair',['support-centroid role','nearest-point role','visible pair distance','full surface gap','full surface authority status'],'no','Norms and same-surface dot-product checks use relative geometry.',session,'def _keypoints','Serve when the provider supplies valid supported points; authority requirements remain unchanged.',parity)
add('extent_ends',['extent-start role','extent-end role','observed endpoint distance'],'no','Endpoint separation is a Euclidean norm.',session,'def _keypoints','Serve when the provider supplies supported endpoints.','test_ground_box_count_witness_and_keypoints')
add('ground room',['support frames','floor height','floor cells','supported cells','cell size','minimum contributing frames','area'],'no','Gravity height and horizontal footprint measurements require no reference heading; the existing rasterizer is retained.','trace_format/room_v314.py','def format_result','Serve unchanged with the same sampled geometry.',parity+'; test_relative_gap_fields_and_ties; test_actual_cpu_session')
add('dist',['distance'],'no','norm(P_b-P_a) is rotation invariant.',calc,'if op == "dist":','Serve unchanged.',calculator)
add('closest',['minimum pair labels','minimum distance'],'no','argmin and norm use pair distances.',calc,'elif op in ("closest", "cam_dist"):','Serve unchanged, including the existing tie rule.',calculator)
add('cam_dist',['point labels','per-point camera distance','minimum label','minimum distance'],'no','norm(camera_i) is independent of the reference yaw.',calc,'elif op in ("closest", "cam_dist"):','Serve unchanged.',calculator)
for call in ('angle (easy/medium/hard/turn)','calculator waypoint turn'):
    add(call,['u horizontal components','v horizontal components'],'yes','The printed vectors have components in the reference horizontal axes.',calc,'if op in (\'angle\', \'turn\') and any','Withhold each vector when an operand has no defined reference heading.',calculator)
    add(call,['dot','signed cross','theta','relative direction/turn category'],'no','Dot and oriented area are invariant under SO(2); atan2 and relative categories follow.',calc,'if op in (\'angle\', \'turn\') and any','Serve unchanged; preserve geometric and rounding-boundary refusals.',calculator)
add('area',['area'],'no','The shoelace signed area is invariant under a common horizontal rotation.',calc,'text = f"area','Serve unchanged.',calculator)
add('all calls',['syntax / non-heading availability status'],'no','Invalid calls, absent geometry and provider failures are independent of reference heading.','student_pilot/carrier_c1_decode.py','def respond(','Preserve typed errors and genuine availability failures.','test_response_status; test_row_audit; test_box_renderer_status_paths')
text=['# Heading dependence','',
    'The public level frame uses y for gravity-up and x/z for horizontal coordinates. World geometry uses z for gravity-up. The table covers every printed field in the decode, shared formatter, calculator, and keypoint paths. Box axes and metric operands remain private and are not additional printed fields.',
    '', 'Each no entry describes the quantity’s coordinate meaning. Quantization, coordinate-wise medians, box-yaw rounding, and room-grid rasterization are retained; they are not mathematically rotation-equivariant at all precision boundaries. Byte-parity tests hold the scene and its numeric representation fixed and change only heading availability. No test claims arbitrary re-rotation preserves every rounded digit.',
    '', 'Tests are in `work/tests_r2/test_heading_r2.py`, with inherited fixture checks in `test_contracts.py` and `test_edges.py`. Results and executed lines are recorded in `out/FINAL_TEST_RESULTS_R2.json` and `out/COVERAGE_DETAIL_R2.json`.',
    '', '| Call | Field | Needs frame-1 heading | Math | Patched-tree location | Undefined-reference behavior | Proof test |', '|---|---|---|---|---|---|---|']
text += ['| '+' | '.join(r)+' |' for r in rows]
text+=['','## Heading-unavailable emitters','',
    'The following source statements create the status. Recognition, parsing, and audit branches do not create additional output. Runtime field emitters use `heading_available`, which reads the bound threshold through `heading_plane_min`; the convention guard remains independent.','']
for rel,needle,why in [
 ('trace_format/contracts.py','def partial_f1','Horizontal components of every partial point or centre.'),
 (calc,"text = 'u heading unavailable",'Calculator horizontal u/v components; scalar results remain.'),
 (head,"return 'f1 centre '+partial_f1",'Pose reference-frame centre components and yaw.'),
 (head,"return f\"f1 centre {vec(self.camera_pose",'Pose yaw of a degenerate queried frame, named explicitly.'),
 (head,"return (f'dx = heading unavailable",'Move horizontal components of a degenerate source frame, named explicitly.'),
 (head,"return 'turn = heading unavailable",'Turn whose endpoint headings are degenerate, with their frame IDs.'),
 (box,"'yaw heading unavailable'",'Box yaw; other box fields continue.'),
 (ground,"raise ValueError('heading unavailable')",'Direct request for complete public centres without the metric-only option; partial formatters use that option.'),
 ('trace_format/contracts.py','def status_text','Generic explicit status formatter, also usable by callers passing this status.')]:
    n=next(i for i,s in enumerate((S/rel).read_text().splitlines(),1) if needle in s)
    text.append(f'- [{rel}:{n}]({T/rel}:{n}): {why}')
(L/'out/HEADING_DEPENDENCE_R2.md').write_text('\n'.join(text)+'\n')
(L/'out/HEADING_FIELDS_R2.json').write_text(json.dumps(dict(source=__file__,columns=['call','field','needs_frame1_heading','math','location','behavior','test'],rows=rows),indent=2)+'\n')
