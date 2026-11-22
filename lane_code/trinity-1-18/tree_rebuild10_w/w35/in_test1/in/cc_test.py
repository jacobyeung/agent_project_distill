"""fix21: the tree's own r1_handover.compare_configs(P's prepare config, N's job config) under a given tree,
for N's config as job 174246 ran it (v.json) and with milestones [100, 200] (top level and recipe) and the plan's export
count. Controls: interval 10800 and wall 64800 must refuse. Usage: cc_test.py <tree> <P config> <N v.json>"""
import sys, json, copy
from pathlib import Path
TREE = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(TREE))
from student_pilot.r1_handover import compare_configs
import student_pilot.r1_handover as H; assert H.__file__.startswith(str(TREE))
# head_init reads each side's pinned init artifact (Orchard only); stubbed to one value for both sides, so the
# optimizer contract still compares every other setting. It does not read the milestones.
H.head_init = lambda cfg, *, replicas=None: 'STUB_SAME_FOR_BOTH'
# The effective camera settings come from pinned preparation receipts (Orchard only); stubbed to one value for both.
H.effective_camera = lambda cfg, candidates, replicas: 'STUB_SAME_FOR_BOTH'
P = json.loads(Path(sys.argv[2]).read_text()); N = json.loads(Path(sys.argv[3]).read_text())
def variant(ms=None, **recipe):
    c = copy.deepcopy(N)
    if ms is not None:
        c['milestones'] = list(ms); c['recipe']['milestones'] = list(ms)
        c['checkpoint_disk_guard'] = dict(c['checkpoint_disk_guard'], planned_weight_exports=len(set(ms)) + int(bool(c['recipe'].get('export_at_stop'))))
    c['recipe'].update(recipe)
    return c
cases = [('as_run_174246', variant()), ('milestones_100_200', variant([100, 200])),
         ('control_interval_10800', variant([100, 200], resume_every_seconds=10800)),
         ('control_wall_64800', variant([100, 200], wall_seconds=64800))]
out = dict(tree=str(TREE), P_milestones=P.get('milestones'), P_recipe_milestones=P['recipe'].get('milestones'), results={})
# The camera-override candidates come from each side's pinned preparation receipt (Orchard only): both sides'
# 'preparation' key is dropped, so camera_overrides compares by plain equality; every other key is compared as in the tree.
Pq = {k: v for k, v in P.items() if k != 'preparation'}
out['dropped_preparation_key'] = [('preparation' in P), ('preparation' in N)]
out['preparation_is_handover_variable'] = 'preparation' in H.HANDOVER_VARIABLE_KEYS
for name, cfg in cases:
    cfg = {k: v for k, v in cfg.items() if k != 'preparation'}
    try:
        compare_configs(Pq, cfg); r = 'PASS'
    except Exception as e:
        r = 'REFUSE ' + type(e).__name__ + ': ' + str(e)[:160]
    out['results'][name] = r
print(json.dumps(out, indent=1))
