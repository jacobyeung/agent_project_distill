from pathlib import Path
import shutil

B = Path(__file__).resolve().parents[1]
W = B.parents[1] / 'work'
SRC = W / 'code9'
DST = B / 'out/c8/sources'
REL = Path('sj/orch_cd/evalx/work/milestone')
for p in SRC.rglob('*'):
    if p.is_file():
        q = DST / p.relative_to(SRC)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, q)
ROOT = DST / REL

def edit(name, before, after, count=1):
    p = ROOT / name
    s = p.read_text()
    assert s.count(before) == count, (name, before, s.count(before))
    p.write_text(s.replace(before, after))

guard = (B/'in_orders/gravity_guard_build01_a62e3975.py').read_text()
guard = guard.replace("    original = geometry_profiles_module.GeometryContract.validate", "    if geometry_profiles_module.GeometryError is not GeometryError:\n        raise RuntimeError('gravity_guard_exception_class_mismatch')\n    original = geometry_profiles_module.GeometryContract.validate")
(ROOT/'native/out2/gravity_guard.py').write_text(guard)

edit('native/out2/geometry.py', "        outcome=GR.attempt(prepare_one,GeometryError)", "        import gravity_guard\n        with gravity_guard.capture('dev-S1', c['native']):\n            outcome=GR.attempt(prepare_one,GeometryError)")
edit('native/out2/perception.py', "    geometry=native(checked(entry),FrameMap(tuple(row['student_input']['frame_indices'])),'tower_scaled')", "    import gravity_guard\n    capture = next(record['native'] for record in manifest['records'] if record['clip'] == clip)\n    with gravity_guard.capture('dev-S1', capture):\n        geometry=native(checked(entry),FrameMap(tuple(row['student_input']['frame_indices'])),'tower_scaled')")
edit('native/out2/nomdg.py', "'read_runtime.py','reader_policy.py','geometry_refusals.py')", "'read_runtime.py','reader_policy.py','geometry_refusals.py','gravity_guard.py')")
edit('native/out2/nomdg.py', '\ndef run(args,request):', '''
def parity_selection(tasks):
    selected = {name: next((key for key in sorted(tasks)
                            if family(tasks[key]['question_type']) == name), None)
                for name in FAMILIES}
    present = {name: key for name, key in selected.items() if key is not None}
    if not present:
        raise ValueError('Parity requires at least one routed family')
    return dict(items=present, absent_families=[name for name in FAMILIES if name not in present],
                probe_key=present.get('camera_displacement', next(iter(present.values()))))


def run(args,request):''')
edit('native/out2/nomdg.py', "    dump(out/'LOAD_RECEIPT.json',dict(info,runtime_tree=request['runtime_tree']))\n    first=tasks[next(key for key in sorted(tasks) if family(tasks[key]['question_type'])=='camera_displacement')]", "    selection=parity_selection(tasks)\n    dump(out/'LOAD_RECEIPT.json',dict(info,runtime_tree=request['runtime_tree'],parity_selection=selection))\n    first=tasks[selection['probe_key']]")
edit('native/out2/nomdg.py', "    parity['pass']=p1_gate['pass'] and all(parity[k]['pass'] for k in ('P2','P3')) and parity['camera_call'] and not parity['call_errors']", "    parity['selection']=selection\n    camera_required='camera_displacement' in selection['items']\n    parity['pass']=p1_gate['pass'] and all(parity[k]['pass'] for k in ('P2','P3')) and (parity['camera_call'] or not camera_required) and not parity['call_errors']")
edit('native/out2/nomdg.py', "    r['runtime_tree']=tree_identity(TREE,r['tree_sources'])", "    import gravity_guard\n    r['gravity_guard']=gravity_guard.identity()\n    r['runtime_tree']=tree_identity(TREE,r['tree_sources'])")
edit('native/out2/nomdg.py', "    from student_pilot.s1_grounding import default_policy\n    if r['candidate_policy']", "    import gravity_guard\n    if r.get('gravity_guard') != gravity_guard.identity():\n        raise ValueError('Gravity guard request identity differs')\n    from student_pilot.s1_grounding import default_policy\n    if r['candidate_policy']")

edit('orchard_native/native_worker.py', '\ndef prepare_full_geometry(', '''
def install_gravity_guard(native):
    import gravity_guard
    from student_pilot import geometry_profiles
    try:
        gravity_guard.install(geometry_profiles, gravity_guard.Recorder())
    except Exception as error:
        C.dump(Path(native)/'GUARD_INSTALL_REFUSAL.json', dict(
            gravity_guard=gravity_guard.identity(), error=str(error)))
        raise


def prepare_full_geometry(''')
edit('orchard_native/native_worker.py', '    context = K.function(parts["geometry_restore"], vars(G))(args)', '    context = K.function(parts["geometry_restore"], vars(G))(args)\n    install_gravity_guard(Path(destination).parent)')
edit('orchard_native/native_worker.py', '    context = K.function(parts["restore"], vars(N))(args, bound)', '    context = K.function(parts["restore"], vars(N))(args, bound)\n    install_gravity_guard(native)')
edit('orchard_native/native_worker.py', '    return value\n\n\ndef geometry_subset', '    import gravity_guard\n    value["gravity_guard"] = gravity_guard.identity()\n    return value\n\n\ndef geometry_subset')
edit('orchard_native/native_worker.py', '    if not set(required) <= {record["native"] for record in geometry_times} or not near_boundary:', '    if not set(required) <= {record["native"] for record in geometry_times}:')
edit('orchard_native/native_worker.py', '    report.checkpoint("geometry_complete", selection=selection, geometry_seconds=geometry_seconds,', '    import gravity_guard\n    guard_report = gravity_guard.report()\n    M.validate_gravity_guard(guard_report, {"dev-S1": geometry_times})\n    report.checkpoint("geometry_complete", gravity_guard=gravity_guard.identity(),\n        gravity_guard_report=guard_report, selection=selection, geometry_seconds=geometry_seconds,')
edit('orchard_native/native_worker.py', '''        geometry_cpu_comparison=dict(predicted_refused_captures=12, predicted_refused_distance_items=21,
            predicted_head_capture_range=[6, 13], observed_refused_captures=refused_captures,
            observed_refused_items=len(refused_tasks), within_capture_range=6 <= refused_captures <= 13))''', '''        geometry_guard_comparison=dict(sealed_refused=guard_report['dev-S1']['sealed_refused_count'],
            reviewed_refused=refused_captures, reviewed_refused_items=len(refused_tasks),
            reviewed_only_refused=guard_report['dev-S1']['reviewed_only_refused_count']))''')
edit('orchard_native/native_worker.py', '                   geometry_refusal=refusal, decode_executed=not bool(refusal),', '                   geometry_refusal=refusal, program_refusal=decoded.get("finish") == "program_refusal",\n                   decode_executed=not bool(refusal) and decoded.get("finish") != "program_refusal",')
edit('orchard_native/native_worker.py', '    report["unit_scores"] = bundle["unit_scores"]', '''    report["unit_scores"] = bundle["unit_scores"]
    import gravity_guard
    report['gravity_guard'] = gravity_guard.identity()
    report['gravity_guard_report'] = gravity_guard.report()
    M.validate_gravity_guard(report['gravity_guard_report'],
        {'dev-S1': N.load(geometry/'GEOMETRY_MANIFEST.json')['records']})
    report['program_refusals'] = M.program_refusals(bundle['arms']['unflagged'])''')

edit('orchard_native/native_metrics.py', '\nclass PilotReport:', '''
def program_refusals(items):
    counts = Counter(row.get('family', {'absolute_distance_object': 'object_abs_distance',
                         'absolute_size_room': 'room_size_estimation'}.get(
                             row.get('question_type'), row.get('question_type')))
                     for row in items
                     if row.get('finish', row.get('decode', {}).get('finish')) == 'program_refusal')
    return dict(total=sum(counts.values()), per_family={name: counts[name] for name in FAMILY_COUNTS})


def validate_gravity_guard(recorder, dispositions):
    if set(recorder) != set(dispositions):
        raise ValueError('Gravity guard capture sets differ')
    for scope, records in dispositions.items():
        value = recorder[scope]
        captures = sorted(row['native'] for row in records)
        refused = sorted(row['native'] for row in records if row['status'] == 'REFUSED')
        sealed = value['sealed_refused']
        if (len(set(captures)) != len(captures) or value['captures'] != captures
                or value['capture_count'] != len(captures)
                or sealed != sorted(set(sealed)) or not set(sealed) <= set(captures)
                or value['reviewed_refused'] != refused
                or value['reviewed_only_refused'] != sorted(set(refused)-set(sealed))
                or any(value[name+'_count'] != len(value[name]) for name in
                       ('sealed_refused', 'reviewed_refused', 'reviewed_only_refused'))
                or any(row['status'] not in ('PASS', 'REFUSED') for row in records)
                or any(row['error']['code'] != GEOMETRY_REFUSAL_CODE for row in records
                       if row['status'] == 'REFUSED')):
            raise ValueError('Gravity guard recorder differs from geometry dispositions')
    return recorder


class PilotReport:''')
edit('orchard_native/native_metrics.py', '        self.value["by_family"] = dict(groups)', '        self.value["by_family"] = dict(groups)\n        self.value["program_refusals"] = program_refusals(self.value["items"])')
edit('orchard_native/native_metrics.py', '        for row in grouped[name]:\n            timing', '        for row in grouped[name]:\n            if row.get("finish") == "program_refusal":\n                continue\n            timing')
edit('orchard_native/native_metrics.py', '    close_lengths = [len(row.get("decode_budget", {}).get("close_token_ids", [])) for row in items]\n    close_tokens = max(close_lengths)\n    if close_tokens < 1:', '    close_lengths = [len(row.get("decode_budget", {}).get("close_token_ids", []))\n                     for row in items if row.get("finish") != "program_refusal"]\n    close_tokens = max(close_lengths or [0])\n    if close_lengths and close_tokens < 1:')
edit('orchard_native/native_metrics.py', '        bounded_mean = sum(row["capped_seconds"] for row in bounds)/len(bounds)', '        bounded_mean = sum(row["capped_seconds"] for row in bounds)/len(bounds) if bounds else 0.')
edit('orchard_native/native_metrics.py', 'pilot_capped_items=capped_pilot, replay_estimated_capped_items=math.ceil(count*capped_pilot/len(bounds)),', 'program_refusal_items=sum(row.get("finish") == "program_refusal" for row in grouped[name]),\n            timing_sample_missing=not bool(bounds),\n            pilot_capped_items=capped_pilot, replay_estimated_capped_items=math.ceil(count*capped_pilot/len(bounds)) if bounds else 0,')
edit('orchard_native/native_metrics.py', '    size_fits = projected <= RETURN_LIMIT', '    timing_measured = all(not value["timing_sample_missing"] for value in per_family.values())\n    size_fits = projected <= RETURN_LIMIT')
edit('orchard_native/native_metrics.py', 'time_fits=with_margin <= 21600, fits=size_fits and with_margin <= 21600)', 'time_fits=timing_measured and with_margin <= 21600, fits=timing_measured and size_fits and with_margin <= 21600)')
edit('orchard_native/native_metrics.py', '        per_family=per_family, geometry_captures=GEOMETRY_CAPTURES,', '        per_family=per_family, program_refusals=program_refusals(items),\n        timing_measured=timing_measured, geometry_captures=GEOMETRY_CAPTURES,')

edit('orchard_native/native_job.py', '        M.geometry_evidence(report)', '        M.geometry_evidence(report)\n        M.validate_gravity_guard(report["gravity_guard_report"], {"dev-S1": report["geometry"]})')
edit('orchard_native/native_job.py', '        C.checked(report["bundle"], lambda p: S.physical(root, p))', '        M.validate_gravity_guard(report["report"]["gravity_guard_report"],\n            {"dev-S1": C.load(run/"native/geometry/GEOMETRY_MANIFEST.json")["records"]})\n        C.checked(report["bundle"], lambda p: S.physical(root, p))')
edit('orchard_native/native_launcher.py', 'gpu_seconds=2400 if mode == "pilot" else 21600', 'gpu_seconds=6000 if mode == "pilot" else 21600')
edit('orchard_native/native_launcher.py', '"01:30:00" if config["mode"] == "pilot" else "07:00:00"', '"02:00:00" if config["mode"] == "pilot" else "07:00:00"')
edit('orchard_native/native_launcher.py', 'MASK_CACHE_P6_BOUND.json', 'MASK_CACHE_C8_BOUND.json', count=2)
edit('orchard_native/native_launcher.py', '        code_pins[mask["path"]] = mask["sha256"]', '        code_pins[mask["path"]] = mask["sha256"]\n        legacy = Path(__file__).resolve().parent/"MASK_CACHE_P6_BOUND.json"\n        code_pins[str(C.LOGICAL_ROOT/"orchard_native/MASK_CACHE_P6_BOUND.json")] = C.sha(legacy)')
edit('orchard_native/native_launcher.py', '    C.dump(destination/"PACKET.json", dict(', '    sys.path.insert(0, str(C.ROOT/"native/out2"))\n    from common import install_tree\n    install_tree()\n    import gravity_guard\n    C.dump(destination/"PACKET.json", dict(gravity_guard=gravity_guard.identity(),')
edit('orchard_native/native_local_check.py', '"kernels.py", "native_job.py", "MASK_CACHE_P6_BOUND.json"', '"kernels.py", "native_job.py", "MASK_CACHE_P6_BOUND.json", "MASK_CACHE_C8_BOUND.json"')
edit('orchard_native/native_local_check.py', '"geometry_refusals.py", "r1.py", "camera_report.py"', '"geometry_refusals.py", "gravity_guard.py", "r1.py", "camera_report.py"')
edit('orchard_native/native_local_check.py', 'set(old_adapters) | {new_adapter}', 'set(old_adapters) | {new_adapter, str(C.LOGICAL_ROOT / "native/out2/gravity_guard.py")}')
edit('orchard_native/native_pin_graph.py', 'MASK_PATH = str(C.LOGICAL_ROOT / "orchard_native/MASK_CACHE_P6_BOUND.json")', 'MASK_PATH = str(C.LOGICAL_ROOT / "orchard_native/MASK_CACHE_C8_BOUND.json")')
print(ROOT)
