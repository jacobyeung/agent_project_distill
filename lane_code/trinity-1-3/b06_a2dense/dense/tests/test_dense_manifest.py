import json
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import dense_manifest as dm  # noqa: E402
from student_pilot.dense_eval import nested_indices  # noqa: E402

import pytest  # noqa: E402


def h(*parts):
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def student(total):
    return [(i * (total - 1)) // 31 for i in range(32)]


def make_world(total=1000, scenes=(('d1', 'vA'),), held_extra=()):
    fm, plan = {}, {'total': {}, 'v': {}, 'a': {}}
    for d, s in scenes:
        m = {}
        for i in student(total):
            m[i] = dict(sha256=h(s, i), path=dm.logical(dm.K6_ROOT, h(s, i)), w=640, h=480)
        for i in held_extra:
            m[i] = dict(sha256=h(s, i), path=dm.logical(dm.K6_ROOT, h(s, i)), w=640, h=480)
        fm[(d, s)] = m
        plan['total'][s] = total
        if d == 'd3':
            plan['a'][s] = dict(u='https://example.invalid/x/lowres_wide.zip', rot='none',
                                need=[[i, 100.0 + i / 10, 1] for i in student(total)])
        else:
            plan['v'][s] = dict(g=d, n=f'{s}.mp4', raw_n=total, need=student(total))
    return fm, plan


def clip(d, s, total, shas=None, fps=24.0, roots=None):
    idx = student(total)
    shas = shas or [h(s, i) for i in idx]
    return dict(sig=h('sig', d, s, total), dataset=d, scene=s, fps=fps, total=total, frame_indices=idx,
                sha256=shas, rows=3, streams={'vqa': 3}, roots=roots or {'/data2/k6tk': 96})


def test_nesting_uses_tree_rule_and_contains_student_set():
    fm, plan = make_world()
    entries, refusals, tv, ta = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    assert not refusals and len(entries) == 1
    e = entries[0]
    assert e['wanted'] == nested_indices(1000, student(1000), 64)
    assert set(student(1000)) <= set(e['wanted']) and len(e['wanted']) == 64
    assert e['origin'] == {'row': 32, 'decode': 32}
    assert sorted(tv['vA']) == sorted(set(e['wanted']) - set(student(1000)))


def test_k6_extras_are_reused_when_they_sit_on_the_rule():
    wanted = nested_indices(1000, student(1000), 64)
    extra = sorted(set(wanted) - set(student(1000)))[:10]
    fm, plan = make_world(held_extra=extra + [5, 7])      # 5 and 7 are off-rule extras: never used
    entries, _, tv, _ = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    e = entries[0]
    assert e['origin'] == {'row': 32, 'k6': 10, 'decode': 22}
    assert 5 not in e['wanted'] and 7 not in e['wanted']


def test_content_key_merges_aliases_and_separates_clocks():
    fm, plan = make_world(scenes=(('d1', 'vA'),))
    entries, _, _, _ = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    got = {(e['scene'], f['source_index']): h('new', f['source_index']) for e in entries for f in e['frames'] if f['sha256'] is None}
    # alias vB of the same recording: identical pins at identical ordinals -> same clip key
    e0 = entries[0]
    alias = dict(e0, scene='vB', sig=dm.signature_key(e0['dataset'], 'vB', e0['fps'], e0['total'], e0['frame_indices'], e0['student_sha256']))
    got.update({('vB', i): sha for (s, i), sha in got.items() if s == 'vA'})
    clips, index, refusals = dm.seal([entries[0], alias], got)
    assert not refusals and len(clips) == 1 and index[alias['sig']] == index[entries[0]['sig']]
    # the same scene on a second clock (another total) is refused against the map clock, never merged
    fm2, plan2 = make_world(total=1000)
    _, refusals2, _, _ = dm.plan_all([clip('d1', 'vA', 2000)], fm2, plan2, {})
    assert [r['code'] for r in refusals2] == ['clock_differs']


def test_two_clock_scene_with_its_own_map_clock_is_its_own_clip():
    fm, plan = make_world(total=1000, scenes=(('d2', 'vC'),))
    fm2, plan2 = make_world(total=2000, scenes=(('d2', 'vD'),))      # same recording, 60 vs 30 fps alias
    fm.update(fm2)
    plan['total'].update(plan2['total'])
    plan['v'].update(plan2['v'])
    entries, refusals, _, _ = dm.plan_all([clip('d2', 'vC', 1000, fps=30.0), clip('d2', 'vD', 2000, fps=60.0)], fm, plan, {})
    assert not refusals
    got = {(e['scene'], f['source_index']): h(e['scene'], 'n', f['source_index']) for e in entries for f in e['frames'] if f['sha256'] is None}
    clips, index, _ = dm.seal(entries, got)
    assert len(clips) == 2 and len(set(index.values())) == 2
    assert {c['fps'] for c in clips.values()} == {30.0, 60.0}


def test_row_pin_that_differs_from_k6_is_kept_and_counted():
    fm, plan = make_world()
    shas = [h('vA', i) for i in student(1000)]
    shas[3] = h('kr9c-variant', 3)
    entries, refusals, _, _ = dm.plan_all([clip('d1', 'vA', 1000, shas=shas, roots={'/data2/kr9c': 32})], fm, plan, {})
    assert not refusals
    e = entries[0]
    assert e['row_pin_differs_from_k6'] == 1
    slot = e['wanted'].index(student(1000)[3])
    assert e['frames'][slot]['sha256'] == shas[3] and e['frames'][slot]['origin'] == 'row'


def test_off_map_and_short_and_invalid_are_refused_with_codes():
    fm, plan = make_world()
    joined = dict(sig='j', dataset='d1', scene='vZ', fps=None, total=None, frame_indices=student(1000),
                  sha256=None, map_joined=True, rows=2, streams={'routing': 2})
    short = clip('d1', 'vA', 50)
    bad = dict(clip('d1', 'vA', 1000), frame_indices=[1] + student(1000)[1:])
    _, refusals, _, _ = dm.plan_all([joined, short, bad], fm, plan, {})
    assert sorted(r['code'] for r in refusals) == ['off_map', 'short_clip', 'student_set_invalid']


def test_map_joined_clip_resolves_through_map_plan_and_fps_authority():
    fm, plan = make_world()
    joined = dict(sig='j', dataset='d1', scene='vA', fps=None, total=None, frame_indices=student(1000),
                  sha256=None, map_joined=True, rows=2, streams={'routing': 2})
    entries, refusals, _, _ = dm.plan_all([joined], fm, plan, {'d1/vA': 24.0})
    assert not refusals and entries[0]['fps'] == 24.0 and entries[0]['total'] == 1000
    assert entries[0]['sig'] == dm.signature_key('d1', 'vA', 24.0, 1000, student(1000), [h('vA', i) for i in student(1000)])


def test_arkit_new_frames_become_range_tasks_with_known_timestamps():
    fm, plan = make_world(scenes=(('d3', 'vE'),))
    entries, refusals, tv, ta = dm.plan_all([clip('d3', 'vE', 1000, fps=10.0)], fm, plan, {})
    assert not refusals and not tv and len(ta['vE']) == 32
    fp = dm.fetch_plan(ta, plan)
    assert fp['vE']['need_ordinals'] == sorted(ta['vE']) and len(fp['vE']['known']) == 32


def test_seal_refuses_duplicate_content_and_missing_frames():
    fm, plan = make_world()
    entries, _, _, _ = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    new = [f['source_index'] for f in entries[0]['frames'] if f['sha256'] is None]
    got = {('vA', i): h('new', i) for i in new}
    got[('vA', new[1])] = got[('vA', new[0])]
    _, _, ref = dm.seal(entries, got)
    assert [r['code'] for r in ref] == ['duplicate_content']
    got.pop(('vA', new[1]))
    _, _, ref = dm.seal(entries, got)
    assert [r['code'] for r in ref] == ['frame_not_produced']


def test_attach_feeds_tree_build_training():
    from student_pilot.r2_dense import build_training
    fm, plan = make_world()
    entries, _, _, _ = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    got = {('vA', f['source_index']): h('new', f['source_index']) for f in entries[0]['frames'] if f['sha256'] is None}
    clips, index, _ = dm.seal(entries, got)
    idx = student(1000)
    row = dict(qid='q1', dataset='d1', scene='vA', student_input=dict(
        fps=24.0, total_num_frames=1000, frame_indices=idx, timestamps=[i / 24.0 for i in idx],
        frames=[dict(path=dm.logical('/data2/kr9c', h('vA', i)), sha256=h('vA', i)) for i in idx]))
    out, key = dm.attach(row, dict(clips=clips, index=index))
    built, clip_key = build_training(out)
    assert clip_key == key
    dense = built['student_input']['geometry_dense']
    assert dense['frame_indices'] == nested_indices(1000, idx, 64)
    # the row keeps its own logical path at student ordinals
    assert dense['frames'][0]['path'].startswith('/data2/kr9c/')


def test_parity_holds_scenes_whose_refetched_student_frames_differ():
    fm, plan = make_world(scenes=(('d3', 'vE'), ('d3', 'vF')))
    entries, _, _, _ = dm.plan_all([clip('d3', 'vE', 1000, fps=10.0), clip('d3', 'vF', 1000, fps=10.0)], fm, plan, {})
    got = {(e['scene'], f['source_index']): h('new', e['scene'], f['source_index']) for e in entries for f in e['frames'] if f['sha256'] is None}
    got[('vE', 0)] = h('vE', 0)              # parity equal
    got[('vF', 0)] = h('different bytes')    # parity differs -> vF held
    par = dm.parity(entries, got)
    assert par['equal'] == 1 and par['differ'] == 1 and par['held_scenes'] == ['vF']


def test_pixel_parity_admits_lsb_differences_and_holds_the_rest(tmp_path):
    fm, plan = make_world(scenes=(('d3', 'vE'), ('d3', 'vF'), ('d3', 'vG')))
    entries, _, _, _ = dm.plan_all([clip('d3', s, 1000, fps=10.0) for s in ('vE', 'vF', 'vG')], fm, plan, {})
    got = {}
    for s in ('vE', 'vF', 'vG'):
        got[(s, 0)] = h('refetched', s)
    p = tmp_path / 'px.jsonl'
    p.write_text('\n'.join(json.dumps(r) for r in [
        dict(s='vE', k=0, byte_equal=False, pinned=h('vE', 0), fetched=h('refetched', 'vE'), max=1, frac=4e-6, ok=True),
        dict(s='vF', k=0, byte_equal=False, pinned=h('vF', 0), fetched=h('refetched', 'vF'), max=9, frac=0.2, ok=False),
    ]) + '\n')
    par = dm.parity(entries, got, dm.load_pixel_parity(str(p)))   # vG has no pixel record -> held
    assert par['pixel_equal'] == 1 and par['differ'] == 2 and par['held_scenes'] == ['vF', 'vG']


def test_review_counterexamples_refuse_clock_conflict_stale_signature_pin_change_and_missing_parity():
    fm, plan = make_world()
    entries, _, _, _ = dm.plan_all([clip('d1', 'vA', 1000)], fm, plan, {})
    e0 = entries[0]
    got = {('vA', f['source_index']): h('new', f['source_index']) for f in e0['frames'] if f['sha256'] is None}
    other = dict(e0, fps=30.0, sig=dm.signature_key(e0['dataset'], 'vA', 30.0, e0['total'], e0['frame_indices'], e0['student_sha256']))
    clips, index, ref = dm.seal([e0, other], got)
    assert len(clips) == 1 and [r['code'] for r in ref] == ['clock_conflict']
    stale = dict(e0, student_sha256=[h('x')] + e0['student_sha256'][1:])
    assert [r['code'] for r in dm.seal([stale], got)[2]] == ['stale_signature']
    changed = dict(e0, frames=[dict(f, sha256=h('y')) if f['source_index'] == e0['frame_indices'][0] else f for f in e0['frames']])
    assert [r['code'] for r in dm.seal([changed], got)[2]] == ['student_pin_differs']
    par = dm.parity([e0], got)
    assert par['checked'] == 0 and par['parity_missing'] == ['vA'] and par['held_scenes'] == ['vA']


def test_wa_dense_plan_capture_uses_traj_rows_and_refuses_clock_mismatch():
    import types
    import wa_dense
    traj = '\n'.join(f'{100.0 + k * 0.1:.6f} 0 0 0 0 0 0' for k in range(200)).encode()
    wa = types.SimpleNamespace(get_range=lambda url, a, b: traj)
    e = dict(u='https://example.invalid/c/lowres_wide.zip', rot='none', need_ordinals=[5, 9],
             known=[[0, 100.0, 1], [10, 101.0, 1], [20, 102.0, 1]])
    entry, meta = wa_dense.plan_capture(wa, 'vX', e, parity_all=False)
    assert [k for k, t, f in entry['need']] == [0, 5, 9, 10] and meta['parity'] == [0, 10]
    assert abs(entry['need'][1][1] - 100.5) < 1e-9
    e_bad = dict(e, known=[[0, 100.0, 1], [10, 101.5, 1]])
    entry, meta = wa_dense.plan_capture(wa, 'vX', e_bad, parity_all=True)
    assert entry is None and meta['error'].startswith('clock')
    e_over = dict(e, need_ordinals=[250])
    entry, meta = wa_dense.plan_capture(wa, 'vX', e_over, parity_all=True)
    assert entry is None and 'past' in meta['error']


def test_canonical_named_pool_row_resolves_to_k6_alias_and_checks_clock():
    fm, plan = make_world()
    plan['v']['vA']['n'] = 'scannet/scene0001_00.mp4'
    joined = dict(sig='j', dataset=None, scene='scannet/scene0001_00', fps=None, total=None,
                  frame_indices=student(1000), sha256=None, map_joined=True, rows=1, streams={'routing_pool': 1})
    entries, refusals, _, _ = dm.plan_all([joined], fm, plan, {})
    assert not refusals and entries[0]['scene'] == 'vA' and entries[0]['dataset'] == 'd1'
    other_clock = dict(joined, frame_indices=student(2000)[:31] + [999])
    _, refusals, _, _ = dm.plan_all([other_clock], fm, plan, {})
    assert refusals and refusals[0]['code'] in ('clock_differs', 'off_map')
