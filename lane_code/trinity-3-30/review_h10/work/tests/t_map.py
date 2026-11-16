"""Item-set check: every devs1_routed item binds to b04's native task (question/answer/room/frames) and to b04's 636 parity keys."""
import json, sys
from pathlib import Path
W = Path('/dev/shm/jjyeung_rv10/full')
from e2e_reader import parity
from h1eval.h10.parity_adapter import map_items
items = json.loads((W/'items/devs1_routed.json').read_text())['items']
settings = dict(tree='/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449', frames_root='/nonexistent')
try:
    mapped, mapping = map_items(items, settings)
except Exception as e:
    print('map_items FAIL', type(e).__name__, str(e)[:300]); sys.exit()
keys = {r['key'] for r in mapping['items']}
b04 = set()
for i in range(3):
    b04 |= set(Path(f'/scratch/jjyeung/orch_n30/b04_e2ehook/parity_kit/keys_part{i}of3.txt').read_text().split())
print('mapped', len(mapped), 'keys', len(keys), 'b04 keys', len(b04), 'equal', keys == b04, 'h1-b04', len(keys-b04), 'b04-h1', len(b04-keys))
