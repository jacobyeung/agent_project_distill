from pathlib import Path
L=Path(__file__).resolve().parents[1]
p=L/'work/real_replay_r2/replay.py';s=p.read_text()
s=s.replace("('real_base' if args.mode == 'base' else 'real_patched')", "('r2_reference' if args.mode == 'base' else 'r2_applied')")
s=s.replace("tree = L / 'work/trees' / ('r2_reference' if args.mode == 'base' else 'r2_applied')", "tree = L/'work/base/work/base/tree_b01ce449' if args.mode == 'base' else L/'work/trees/r2_applied'")
s=s.replace("'work/tests'", "'work/tests_r2'")
s=s.replace('from fixtures_contracts import response, masks','from fixtures_contracts import response, masks, head_state')
s=s.replace("'out/real_replay'","'out/real_replay_r2'")
s=s.replace("'work/real_replay/audit'","'work/real_replay_r2/audit'")
s=s.replace('session.bind_state(SimpleNamespace(verify_session=None))','session.bind_state(head_state(geo, owner))')
s=s.replace("    row['size_lines'] =",'''    own_frames = [int(k)+1 for k in np.flatnonzero(planes >= .3) if k > 0]
    assert len(own_frames) >= 2, 'two_defined_nonreference_headings_required'
    i, j = own_frames[:2]
    row['relative_frames'] = [i, j]
    k = spec['display_frame']
    calls = dict(move=f'<move from={i} to={j}>', turn=f'<turn from={i} to={j}>',
                 pose=f'<pose frame={j}>', depth=f'<depth_at frame={k} pts=[[300,400],[650,420],[420,700]]>')
    for label, call in calls.items():
        row['responses'][label] = response(session, call)
    labels = list(session.registry._points)[-3:]
    call = f'<angle S={labels[0]} F={labels[1]} Q={labels[2]} rule=hard>'
    row['responses']['angle'] = response(session, call)
    row['head_calls'] = dict(calls, angle=call)
    if args.mode == 'on':
        from student_pilot.carrier_c1_decode import respond
        # Force only the availability policy OFF on the same readout, after the ON guard admitted it.
        with contract_epoch(False):
            row['heading_defined_computation'] = {name: respond(text, session.registry, session.state.geometry)[0]
                for name, text in calls.items() if name != 'depth'}
        row['heading_plane_min'] = session.heading_plane_min
    row['size_lines'] =''')
p.write_text(s)
p=L/'work/real_replay_r2/summarize.py';s=p.read_text().replace("'out/real_replay'","'out/real_replay_r2'")
s=s.replace("'work/real_replay/replay.py'", "'work/real_replay_r2/replay.py'").replace("'work/tests/fixtures_contracts.py'", "'work/tests_r2/fixtures_contracts.py'")
s=s.replace("    rows.append(dict(capture=key",'''    if n['guard'] == 'pass':
        for name in ('move', 'turn'):
            check(key, 'relative_'+name+'_served', 'heading unavailable' not in n['responses'][name] and 'error:' not in n['responses'][name])
            check(key, 'relative_'+name+'_defined_computation_byte_parity', n['responses'][name] == n['heading_defined_computation'][name])
        check(key, 'depth_camera_and_spread_served', 'cam' in n['responses']['depth'] and 'spread ' in n['responses']['depth'])
        check(key, 'angle_scalar_served', 'theta ' in n['responses']['angle'] and 'dot ' in n['responses']['angle'])
        if not n['heading_geometrically_defined']:
            check(key, 'pose_heading_fields_withheld', 'yaw heading unavailable' in n['responses']['pose'])
            check(key, 'centre_camera_and_spread_served', 'cam' in n['responses']['centre'] and 'spread ' in n['responses']['centre'])
            check(key, 'box_support_served', all('frames ' in n['responses'][name] for name in ('chair_box','table_box')))
    rows.append(dict(capture=key''')
p.write_text(s)
(L/'out/real_replay_r2').mkdir(exist_ok=True)
# Inventory is immutable evidence of the same capture inputs, copied with its provenance.
(L/'out/real_replay_r2/CAPTURE_INVENTORY.json').write_bytes((L/'out/real_replay/CAPTURE_INVENTORY.json').read_bytes())
