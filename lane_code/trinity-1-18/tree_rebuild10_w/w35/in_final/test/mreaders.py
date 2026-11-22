"""fix21: every reader of the milestones on N's path, run by the tree's own functions on CPU with the TEST kit's
configurations (milestones [100, 200]). Usage: mreaders.py <new tree> <kit> <P config> <job v.json with [100,200]>"""
import sys, json, copy, base64, hashlib
from pathlib import Path
TREE, KIT, PC, VJ = (Path(a).resolve() for a in sys.argv[1:5]); sys.path.insert(0, str(TREE))
def cap(p):
    c = json.loads(Path(p).read_text()); return json.loads(base64.b64decode(c['payload']))
C, N, Y, P, V = cap(KIT/'k/c.json'), cap(KIT/'k/n.json'), cap(KIT/'k/y.json'), json.loads(PC.read_text()), json.loads(VJ.read_text())
out = {}
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.checkpoint_space import plan
out['1_config_fields'] = {name: dict(milestones=cfg['milestones'], recipe_milestones=cfg['recipe']['milestones'],
    guard=cfg['checkpoint_disk_guard']) for name, cfg in (('k/c.json', C), ('k/n.json', N), ('job v (174246 + [100,200])', V))}
out['2_recipe_for'] = {name: recipe_for(cfg)['milestones'] for name, cfg in (('c', C), ('n', N), ('v', V), ('P', P))}
out['3_disk_plan_entry_check_host_runtime_assertion'] = {name: plan(recipe_for(cfg), retained_archive_copies=1) == cfg['checkpoint_disk_guard']
    for name, cfg in (('c', C), ('n', N), ('v', V))}
from launch_r1.entry import check_host_runtime
try:
    res = dict(assertions={}); check_host_runtime(C, dict(binaries=[]), res); r = 'returned'
except Exception as e:
    r = 'raised after the disk plan: ' + type(e).__name__ + ': ' + str(e)[:100]
out['3b_entry_check_host_runtime_on_c'] = dict(disk_plan=res['assertions'].get('disk_plan'), rest=r)
import student_pilot.r1_training as R, student_pilot.r1_persisted as RP, student_pilot.r1_coverage as RC
RP.init_policy = lambda v: None; RC.validate_binding = lambda c: None
scale = C['r1_training']['weight_scale']; R.pinned = lambda p: p; R.load = lambda p: {'weight_scale': scale}
for name, cfg in (('c', C), ('n', N)):
    try: R.validate(copy.deepcopy(cfg)); out.setdefault('4_r1_training_validate_line98', {})[name] = 'PASS'
    except Exception as e: out.setdefault('4_r1_training_validate_line98', {})[name] = 'REFUSE ' + str(e)[:100]
rec = recipe_for(V)
out['5_trainer_export_schedule_run_steps'] = dict(
    m0_export_at_start=(0 in rec['milestones']),
    milestone_exports=[s for s in range(1, rec['steps'] + 1) if s in rec['milestones']],
    stop_export=bool(rec.get('export_at_stop')),
    budget_pending_export_steps=[s for s in range(1, rec['steps'] + 1) if s in rec['milestones']],
    note='carrier_c1_run.py:2359 (0 in milestones), 2438 (pending), 2440 (next_cost: step+1 in milestones or export_at_stop, the latter true so unchanged), 2456 (export at step in milestones or at the stop)')
import student_pilot.r1_handover as H
H.head_init = lambda cfg, *, replicas=None: 'STUB'; H.effective_camera = lambda c, k, r: 'STUB'
strip = lambda d: {k: v for k, v in d.items() if k != 'preparation'}
for name, cfg in (('v', V), ('n', N)):
    try: H.compare_configs(strip(P), strip(cfg)); r = 'PASS'
    except Exception as e: r = 'REFUSE ' + str(e)[:120]
    out.setdefault('6_compare_configs_P_vs', {})[name] = r
out['6b_milestones_is_handover_variable'] = 'milestones' in H.HANDOVER_VARIABLE_KEYS
out['8_r1_persisted_122_reads_P_config'] = dict(P_milestones=recipe_for(P)['milestones'], init_step_400_in=400 in recipe_for(P)['milestones'])
objects = Y['objects']; job = '0'
expected = {k + '.j' + job + f'.part{i:02d}-of-04' for k in objects.values() for i in range(4)}
out['10_upload_planner_sessions'] = dict(objects=len(objects), sessions=len(expected),
    milestone_objects=sorted(k for k in objects if k.startswith('m') and k[1:].isdigit()),
    written_by_this_leg=sorted(k for k in objects if k in ('m' + str(s) for s in rec['milestones'])) + ['mstop/mstopB/mstopC for the stop export', 'ck00..ck15, ckstop', 'o', 'u'],
    note='pc.py validate_sessions requires exactly 4 sessions per k/y.json object; k/y.json is unchanged, so the count stays 112 and m400, m600, m800, m1000 (16 sessions) go unused')
print(json.dumps(out, indent=1, default=str))
