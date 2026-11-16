"""Inventory current output statements and classify each public field."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[1];T=L/'work/trees/r5_applied';O=L/'out'
modules=['trace_format/contracts.py','trace_format/calculator.py','student_pilot/carrier_c1_decode.py','student_pilot/carrier_c1_routing.py',
         'student_pilot/ground_lifting.py','trace_format/ground_v313.py','trace_format/box_v313.py',
         'trace_format/room_v314.py','trace_format/ground_v312.py','student_pilot/ground_sources.py']
inventory=[]
for rel in modules:
    p=T/rel;text=p.read_text();tree=ast.parse(text)
    statements=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Return) or isinstance(node,(ast.Assign,ast.AugAssign)) and any(
                isinstance(n,ast.Name) and n.id in ('text','line','lines','body','parts') for n in ast.walk(node)):
            statements.append(dict(line=node.lineno,statement=ast.get_source_segment(text,node)))
    inventory.append(dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),statements=statements))
calc=ast.parse((T/'trace_format/calculator.py').read_text())
fn=next(n for n in calc.body if isinstance(n,ast.FunctionDef) and n.name=='format_command')
ops=ast.literal_eval(next(n for n in fn.body if isinstance(n,ast.Assign) and n.targets[0].id=='keys').value)
assert set(ops)=={'dist','closest','cam_dist','angle','turn','area'}
(O/'OUTPUT_INVENTORY_R5.json').write_text(json.dumps(dict(calculator_operations=sorted(ops),sources=inventory),indent=2))
rows=[]
def add(call,fields,need,why,behavior,test,source):
    for field in fields.split('|'):
        rows.append((call,field,need,why,behavior,test,source))
calcsrc='trace_format/calculator.py';head='student_pilot/carrier_c1_routing.py';ground='trace_format/ground_v313.py';box='trace_format/box_v313.py'
for call in ('depth_at','ground centre','ground instances','gap witness','surface_pair points','extent_ends points'):
    add(call,'point label|camera frame|camera x|camera y|camera z|spread','no','Camera coordinates and observed depth use the named camera.','Serve.','test_all_relative_head_pairs; test_ground_box_count_witness_and_keypoints',calcsrc)
    add(call,'f1 x|f1 z','yes','Horizontal components use the reference heading.','Print heading unavailable when reference heading is undefined.','test_ground_box_count_witness_and_keypoints',calcsrc)
    add(call,'f1 y','no','Height is the projection onto gravity.','Serve.','test_all_ground_fields_match_defined_computation',calcsrc)
add('pose(k), k != reference','centre x|centre z','yes','Centre coordinates depend on reference heading, not k heading.','Withhold only if reference heading is undefined.','test_decode_attacks_and_move_source_distance',head)
add('pose(k)','centre y','no','Height projects displacement onto gravity.','Serve.','test_decode_attacks_and_move_source_distance',head)
add('pose(k), k != reference','yaw','yes; also k','Relative yaw needs both headings.','Withhold if either required heading is undefined.','test_decode_attacks_and_move_source_distance',head)
add('pose(reference)','centre x|centre y|centre z|yaw','no','The reference pose is the identity.','Serve identity even at nadir.','test_pose_identity_and_later_centre',head)
add('move(i,j)','dx|dz','only when i is reference','Components use source i heading.','Withhold if i heading is undefined.','test_decode_attacks_and_move_source_distance',head)
add('move(i,j)','dy|distance','no','Gravity projection and Euclidean norm need no heading.','Serve; retain sealed distance rounding where its basis exists.','test_move_nadir_distance_retains_sealed_rounding',head)
add('turn(i,j)','signed angle','only when an endpoint is reference','Relative yaw needs endpoint headings.','Withhold if either endpoint heading is undefined.','test_decode_attacks_and_move_source_distance',head)
for call in ('ground centre','ground box'):
    add(call,'name|support frames|best frame|size length|size width|size height','no','Support and physical extent do not require reference heading.','Serve.','test_all_ground_fields_match_defined_computation',box if call.endswith('box') else 'student_pilot/ground_lifting.py')
add('ground instances','count|instance ordinal|first frame','no','Image membership and order do not use heading.','Serve.','test_all_ground_fields_match_defined_computation',ground)
add('ground box','box label|instance count','no','Registry identifiers and enumeration do not use heading.','Serve.','test_ground_box_count_witness_and_keypoints',box)
add('ground box','centre x|centre z|yaw','yes','Horizontal centre and orientation use the reference basis.','Print heading unavailable.','test_all_ground_fields_match_defined_computation',box)
add('ground box','centre y','no','Height uses gravity.','Serve.','test_all_ground_fields_match_defined_computation',box)
for call in ('mask gap','box gap','camera gap'):
    add(call,'distance|candidate names|candidate distances|minimum names including ties|minimum distance','no','Distances use relative geometry.','Serve; scalar rounding remains unchanged.','test_relative_gap_fields_and_ties; test_actual_cpu_session',box if call!='mask gap' else ground)
add('surface_pair / extent_ends','role|visible distance|full surface gap|authority status','no','Roles are semantic labels; supported distances use relative geometry.','Serve with existing provider and authority checks.','test_all_ground_fields_match_defined_computation',ground)
add('ground room','support frames|floor height|floor cell count|supported cell count|cell size|minimum frames|area','no','Gravity and the floor footprint define these outputs. Grid rasterization can vary at cell boundaries.','Serve; retain floor-grid quantization.','test_all_ground_fields_match_defined_computation','trace_format/room_v314.py')
add('dist','distance','no','Euclidean norm is rotation invariant before coordinate rounding.','Serve arithmetic from stable private operands when reference heading is unavailable.','test_calculator_field_scope_and_shared_implementation; test_rotated_calculator_fields',calcsrc)
add('closest','winning labels|minimum distance','no','Pairwise Euclidean comparison requires no heading.','Serve rounded operand arithmetic.','test_calculator_field_scope_and_shared_implementation',calcsrc)
add('cam_dist','point labels|each distance|minimum label|minimum distance','no','Camera norms never use reference heading.','Serve.','test_calculator_field_scope_and_shared_implementation',calcsrc)
for call in ('angle (easy, medium, hard)','waypoint turn'):
    add(call,'u x|u z|v x|v z','yes','Printed horizontal vector components rotate with the reference basis.','Print u heading unavailable; v heading unavailable if any operand lacks heading.','test_calculator_field_scope_and_shared_implementation',calcsrc)
    add(call,'dot|signed cross|theta|direction label','no in exact arithmetic','Common horizontal rotation preserves dot and cross before operand rounding.','Serve arithmetic from the shared stable private metric basis.','test_rotated_calculator_fields; test_calculator_field_scope_and_shared_implementation (PASS)',calcsrc)
add('area','area','no in exact arithmetic','Shoelace area is rotation invariant before coordinate rounding.','Serve shoelace arithmetic from the shared stable private metric basis.','test_rotated_calculator_fields; test_calculator_field_scope_and_shared_implementation (PASS)',calcsrc)
add('all decode paths','syntax error|unknown label error|availability status|object name|image pixel coordinates|mask probability','no','Grammar, registry membership and image-space observations do not require heading.','Retain typed errors and availability text; rerender depth validates arguments uniformly.','test_rerender_depth_arguments; test_model_errors_use_runtime_text','student_pilot/carrier_c1_decode.py')
lines=['The vector-heading leak is fixed. Private operands use a stable nonreference camera basis before rounding. The depth and grounded-point probes preserve every served calculator field across reference-frame rotations.',
       f'Source enumeration: [OUTPUT_INVENTORY_R5.json]({O}/OUTPUT_INVENTORY_R5.json). The inventory reads current output statements and calculator operations directly from code; the table does not inherit the prior heading table.',
       f'Rotation evidence: [ROTATED_ANGLE_R5.json]({L}/work/test_artifacts_r5/ROTATED_ANGLE_R5.json). The separate reviewer heading attack is [HEADING_ATTACK_R5.json]({L}/work/test_artifacts_r5/HEADING_ATTACK_R5.json).',
       '| Output | Field | Needs reference heading? | Why | Current behavior | Test | Source |',
       '|---|---|---|---|---|---|---|']
for call,field,need,why,behavior,test,source in rows:
    lines.append(f'| {call} | {field} | {need} | {why} | {behavior} | {test} | [{source}]({T/source}) |')
lines += ['',f'The generator selects the same calculator under ON. Under OFF it retains the standalone sealed calculator. The default threshold remains configuration-bound; see [contracts.py]({T}/trace_format/contracts.py). No arithmetic JSON fields are injected separately into the language model.']
(O/'HEADING_DEPENDENCE_R5.md').write_text('\n\n'.join(lines[:3])+'\n\n'+'\n'.join(lines[3:])+'\n')
