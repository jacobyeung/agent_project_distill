"""Independent probes for M1 (deferred refusal), S1 (policy byte identity), S2 (changed-line receipt).

Usage: r2_probes.py TREE   (A = base+PATCH_A, V1 = +PATCH_CAMFORM, C = +PATCH_CAMFORM2, C2 = base+PATCH_A2+CAMFORM2)
"""
from pathlib import Path
import sys, json, os, sqlite3, shutil
from unittest.mock import patch
W = Path(__file__).resolve().parent
tree = sys.argv[1]; T = W/('tree_'+tree)
sys.path.insert(0, str(T)); sys.dont_write_bytecode = True
P = W/'probe'/tree
if P.exists(): sys.exit('exists '+str(P))
P.mkdir(parents=True)
import torch; torch.set_num_threads(4)
from student_pilot import r1_coverage, r1_training, carrier_c1_run, r1_routing
from student_pilot.p3_provenance import file_pin
from student_pilot.carrier_c1_routing import render, ROUTING_SCHEMA
from launch_r1 import entry, build as kit_build, production_proof
has_form = (T/'student_pilot/r1_camera_trace_form.py').exists()
POLICY_SRC = W/'tree_C/configs/r1_camera_trace_form_v1.json'
raw_policy = POLICY_SRC.read_bytes()
(P/'policy.json').write_bytes(raw_policy); good = file_pin(P/'policy.json')
res = dict(tree=tree, has_camera_module=has_form, policy_sha256=good['sha256'])

def outcome(fn):
    try:
        r = fn(); return 'RETURN:'+repr(r)[:100]
    except AssertionError as e:
        return 'GUARD_HIT:'+str(e)
    except BaseException as e:
        return type(e).__name__+':'+str(e)[:140]

def guards():
    """Fail loudly if any pin is read or other r1 validation runs before the refusal."""
    ps = []
    for name, mod in list(sys.modules.items()):
        if (name.startswith('student_pilot') or name.startswith('launch_r1')) and hasattr(mod, 'pinned'):
            ps.append(patch.object(mod, 'pinned', side_effect=AssertionError('pinned() called in '+name)))
    ps.append(patch('student_pilot.r1_persisted.init_policy', side_effect=AssertionError('init_policy() ran')))
    return ps

# ---------------- M1 ----------------
cases = {'valid_pin': good, 'string': 'not-a-pin', 'None': None, 'False': False, 'empty_dict': {}, 'list': [],
         'zero': 0, 'empty_str': '', 'missing_file': {'path': str(P/'nope.json'), 'sha256': '0'*64},
         'extra_key': {**good, 'x': 1}}
m1 = {}
for cname, field in cases.items():
    cfg = {'r1_training': {'routing_slices': 'deferred_first_boundary', 'camera_trace_form': field}}
    row = {}
    cfgfile = P/('cfg_'+cname+'.json'); cfgfile.write_text(json.dumps(cfg))
    callers = {
        'r1_coverage.deferred': lambda: r1_coverage.deferred(cfg),
        'r1_coverage.deferred(read_pins)': lambda: r1_coverage.deferred(cfg, read_pins=True),
        'r1_coverage.validate_binding': lambda: r1_coverage.validate_binding(cfg),
        'r1_coverage.source_names': lambda: r1_coverage.source_names({}, cfg),
        'r1_coverage.routing_request': lambda: r1_coverage.routing_request(cfg, {}),
        'r1_training.validate': lambda: r1_training.validate(cfg),
        'carrier_c1_run.validate': lambda: carrier_c1_run.validate(cfg),
        'launch_r1.entry.admit': lambda: entry.admit(cfg),
        'launch_r1.entry.frame_host': lambda: entry.frame_host(cfg, P/('fh_'+cname), {}),
        'launch_r1.build.build': lambda: kit_build.build(cfgfile, P/'inputs', P/('kit_'+cname)),
    }
    ps = guards()
    for p in ps: p.start()
    try:
        for k, fn in callers.items(): row[k] = outcome(fn)
    finally:
        for p in ps: p.stop()
    row['frame_host_root_created'] = (P/('fh_'+cname)).exists()
    row['kit_output_created'] = (P/('kit_'+cname)).exists()
    # Production proof: staging check stubbed; deferred() is the first config check after it.
    with patch.object(production_proof, 'verify_staging', return_value={}):
        r = production_proof._run({'config': file_pin(cfgfile)}, P/('proof_'+cname))
    row['production_proof'] = dict(status=r['status'], refusal=r.get('refusal'), steps=r['steps'])
    m1[cname] = row
res['M1_deferred_with_field'] = m1
ctrl = {}
ctrl['deferred_absent_field'] = outcome(lambda: r1_coverage.deferred({'r1_training': {'routing_slices': 'deferred_first_boundary'}}))
decl = P/'decl.json'; decl.write_text(json.dumps(dict(schema='r1-routing-slices-v1', bound=[], deferred={k: 'probe' for k in r1_coverage.ROUTING_FAMILIES})))
dcfg = {'r1_training': {'routing_slice_declaration': file_pin(decl), 'camera_trace_form': good}}
ctrl['declaration_with_field_deferred'] = outcome(lambda: r1_coverage.deferred(dcfg))
ctrl['declaration_with_field_validate'] = outcome(lambda: r1_training.validate(dcfg))
ctrl['declaration_with_bad_pin_validate'] = outcome(lambda: r1_training.validate({'r1_training': {'routing_slice_declaration': file_pin(decl), 'camera_trace_form': 'not-a-pin'}}))
ctrl['both_modes_with_field'] = outcome(lambda: r1_coverage.deferred({'r1_training': {'routing_slices': 'deferred_first_boundary', 'routing_slice_declaration': file_pin(decl), 'camera_trace_form': good}}))
ctrl['bad_slices_value_with_field'] = outcome(lambda: r1_coverage.deferred({'r1_training': {'routing_slices': 'other', 'camera_trace_form': good}}))
ctrl['full_mode_with_field_deferred'] = outcome(lambda: r1_coverage.deferred({'r1_training': {'camera_trace_form': good}}))
res['M1_controls'] = ctrl

# ---------------- S1 ----------------
def mkrow(qid, kind, texts, answer='30'):
    events = [dict(kind=k, text=t) for k, t in texts] + [dict(kind='tool_call', call_id='c', token='<turn from=1 to=2>'),
              dict(kind='tool_response', call_id='c', text='turn = +30 deg')]
    target, spans = render(events, answer)
    return dict(qid=qid, dataset='d1', scene='fixture_clean', target=target,
                student_input=dict(question='probe question', options=['A. left', 'B. right']),
                routing=dict(question_type=kind, events=events, answer=answer, gt_answer=answer, tool_output_spans=spans))

def compose(rows, r1, out):
    db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i, r in enumerate(rows): db.execute('INSERT INTO rows VALUES(?,?,?)', (i, json.dumps(r), '{}'))
    db.commit(); bp = P/(out.name+'_base.sqlite'); bp.write_bytes(db.serialize()); db.close()
    bj = P/(out.name+'_base.json'); bj.write_text(json.dumps(dict(schema=ROUTING_SCHEMA, scene_role='train', heldout_overlap=0, database=file_pin(bp), division=None)))
    with patch.object(r1_routing, 'Filters') as f:
        f.return_value.reason.side_effect = lambda row, stream: 'probe_exclusion' if row['qid'] == 'excluded' else None
        return r1_routing.compose(file_pin(bj), {}, [], {'r1_training': r1}, out)

if has_form:
    from student_pilot import r1_camera_trace_form as M
    obj = json.loads(raw_policy)
    variants = {
        'exact_copy_other_path': raw_policy,
        'indent4': (json.dumps(obj, indent=4)+'\n').encode(),
        'sort_keys': (json.dumps(obj, indent=2, sort_keys=True)+'\n').encode(),
        'compact': json.dumps(obj, separators=(',', ':')).encode(),
        'no_trailing_newline': raw_policy.rstrip(b'\n'),
        'extra_trailing_newline': raw_policy+b'\n',
        'crlf': raw_policy.replace(b'\n', b'\r\n'),
        'tab_indent': raw_policy.replace(b'\n  ', b'\n\t'),
        'unicode_escape': raw_policy.replace(b'"CAM-ROT', b'"\\u0043AM-ROT', 1),
        'utf8_bom': b'\xef\xbb\xbf'+raw_policy,
    }
    s1 = {}
    for name, b in variants.items():
        p = P/('pol_'+name+'.json'); p.write_bytes(b)
        try: same_json = json.loads(b.decode('utf-8-sig')) == obj
        except Exception: same_json = None
        s1[name] = dict(bytes_equal=b == raw_policy, json_equal=same_json, outcome=outcome(lambda: M.CameraTraceForm(file_pin(p)) and 'ACCEPTED'))
    s1['uppercase_sha_pin'] = outcome(lambda: M.CameraTraceForm({**good, 'sha256': good['sha256'].upper()}) and 'ACCEPTED')
    st = P/'pol_stale.json'; st.write_bytes(raw_policy); stpin = file_pin(st); st.write_bytes(variants['indent4'])
    s1['stale_bytes'] = outcome(lambda: M.CameraTraceForm(stpin) and 'ACCEPTED')
    s1['module_constant'] = dict(POLICY_SHA256=getattr(M, 'POLICY_SHA256', None), file_matches=getattr(M, 'POLICY_SHA256', None) == good['sha256'], POLICY_equals_file=M.POLICY == obj)
    out = P/'compose_reformatted'
    s1['compose_with_indent4'] = outcome(lambda: compose([mkrow('r1', 'camera_rotation', [('plan', 'The turn is '+M.ROT_OLD)])],
        {'routing_slice_declaration': file_pin(decl), 'camera_trace_form': file_pin(P/'pol_indent4.json')}, out))
    s1['compose_output_dir_created'] = out.exists()
    res['S1'] = s1

    # ---------------- S2 ----------------
    R = M.ROT_OLD
    dirtext = 'Scoring each option by the matching component: backward = -dz = -0.32 m; forward = dz = 0.32 m.'
    s2cases = {
        'plan_plus_canonical': ('camera_rotation', [('plan', 'The turn is '+R), ('canonical_text', 'Again '+R)]),
        'two_adjacent_canonical': ('camera_rotation', [('canonical_text', 'X '+R), ('canonical_text', ' Y '+R)]),
        'multiline_plan': ('camera_rotation', [('plan', 'a '+R+'\nb '+R)]),
        'same_line_twice': ('camera_rotation', [('plan', R+' '+R)]),
        'direction_two_lines': ('camera_movement_direction', [('plan', 'Scoring each option by the matching component: backward = -dz = -0.32 m;\nleft = -dx = 1.5 m.')]),
        'direction_two_events': ('camera_movement_direction', [('plan', dirtext), ('canonical_text', dirtext)]),
        'direction_single': ('camera_movement_direction', [('plan', dirtext)]),
        'rotation_single': ('camera_rotation', [('plan', 'The turn is '+R)]),
        'no_match': ('camera_rotation', [('plan', 'Nothing to change.')]),
    }
    s2 = {}
    for name, (kind, texts) in s2cases.items():
        row = mkrow(name, kind, texts); new, ids = M.rewrite_row(row)
        form = M.CameraTraceForm(good); form.record(row, ids); rc = form.receipt({'database': good})
        tl = sum(a != b for a, b in zip(row['target'].split('\n'), new['target'].split('\n'), strict=True))
        s2[name] = dict(ids=ids, target_lines_changed=tl, **{k: rc.get(k) for k in ('rewritten_base_rows', 'rewritten_base_rows_by_rule', 'changed_base_lines', 'changed_base_lines_by_type', 'changed_base_lines_by_rule')})
    rows = [mkrow(n, *s2cases[n]) for n in ('plan_plus_canonical', 'direction_two_lines', 'rotation_single', 'no_match')] + \
           [dict(mkrow('excluded', *s2cases['plan_plus_canonical']), qid='excluded')]
    r = outcome(lambda: compose(rows, {'routing_slice_declaration': file_pin(decl), 'camera_trace_form': good}, P/'compose_s2'))
    s2['compose_outcome'] = r[:60]
    if (P/'compose_s2/receipt.json').exists():
        rec = json.loads((P/'compose_s2/receipt.json').read_text())
        s2['compose_receipt'] = {k: rec.get('camera_trace_form', {}).get(k) for k in ('admitted_base_rows_by_type', 'rewritten_base_rows', 'rewritten_base_rows_by_rule', 'changed_base_lines', 'changed_base_lines_by_type', 'changed_base_lines_by_rule')}
        s2['compose_count_refused'] = (rec['count'], rec['refused'])
    res['S2'] = s2
(W/('R2_PROBES_'+tree+'.json')).write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
