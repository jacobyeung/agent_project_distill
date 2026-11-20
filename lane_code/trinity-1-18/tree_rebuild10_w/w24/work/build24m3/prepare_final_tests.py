from common import *
k=D/'planner_scene_tiny/kit'
for rel in ('b/pl.py','b/sc.py','b/cs.py','b/sv.py'):replace(k/rel,(kit('qd')/rel).read_bytes())
p=D/'planner_scene_tiny/node/p/i';p.rename(L/'attic/build24m3/planner_tiny_i3')
s=(D/'planner_scene_tiny.py').read_text()
needle="assert not (root/'q').exists()"
s=s.replace(needle,needle+"\nassert J.load(root/'i/sc.json')['spec']['pool_manifest']==J.load(cfg['s1_routing']['selection']['path'])['manifest']")
(D/'planner_scene_verified.py').write_text(s)
# Refresh hidden-path clones with all final sealed helper bodies.
for name in ('q','n','n_go','qd'):
 k=D/'hidden'/name
 for rel in ('b/pl.py','b/sc.py','b/cs.py','b/sv.py'):replace(k/rel,(kit(name)/rel).read_bytes())
 for rel in ('BUILD.json','SHA256SUMS.txt'):replace(k/rel,(k/rel).read_bytes())
 reseal(k)
s=(D/'hidden_run3.py').read_text().replace('_final3','_verified')
(D/'hidden_verified.py').write_text(s)
