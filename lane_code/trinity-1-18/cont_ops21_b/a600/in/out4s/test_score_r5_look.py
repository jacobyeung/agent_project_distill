"""H3 level follows the look: 99.29% at step 200, 99.82% later (PRELAUNCH_CARD_R1.md line 19).
Usage: python test_score_r5_look.py MODULE   (score_r5_look passes; score_r5_400 fails: it decides at 99.29% for every look)."""
import importlib, sys
sys.path.insert(0, '.'); name = sys.argv[1]; sys.argv = ['x']
M = importlib.import_module(name)
# 36 rooms x 4 items: 21 items -10 pp (rooms 0-5), one +10 pp (room 35): 99.29% wholly below zero, 99.82% not.
items = {'k%d' % i: dict(room_key='r%d' % (i // 4)) for i in range(144)}
cur = {k: 0.0 for k in items}; base = {k: 0.0 for k in items}
for i in range(21): cur['k%d' % i] = -0.1
cur['k143'] = 0.1
M.metrics = lambda rows, its, keys: (dict(completed=len(keys)), {k: rows[k] for k in keys})
def decide(step):
    M.STEP = step
    if hasattr(M, 'level_for'): M.LEVEL = M.level_for(step)
    r = M.compare(cur, base, items, sorted(items), 'synthetic')
    return r.get('harm_look', r['harm9929']), r
h200, r200 = decide(200); h400, r400 = decide(400); h600, _ = decide(600)
print('99.29%', r400['paired']['ci9929'], 'look', r400['paired'].get('ci_look'), 'decisions 200/400/600', h200, h400, h600)
assert h200 is True, 'step 200 must decide at 99.29% (wholly below zero here)'
assert h400 is False and h600 is False, 'later looks must decide at 99.82% (interval reaches above zero here)'
print('PASS')
