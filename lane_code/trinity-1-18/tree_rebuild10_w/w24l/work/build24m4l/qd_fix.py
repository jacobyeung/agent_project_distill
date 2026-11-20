from common import *
from student_pilot.carrier_c1_run import identity
from student_pilot.r1_persisted import init_policy
from copy import deepcopy
k=kit('qd')
for rel in ('k/c.json','k/n.json'):
 cfg=J.load(k/rel);cfg['r1_training']['proof_mode']='train';cap(k/rel,cfg)
 assert init_policy(cfg['r1_training'])=='step400_export_weights_fresh_v1'
 assert cfg==J.load(kit('n')/rel),rel
p=k/'b/h.py';replace(p,p.read_text().replace(".get('proof_mode')!='q'",".get('proof_mode')!='train'"))
v=J.load(k/'BUILD.json');v['config_sha256']=J.sha(k/'k/c.json');cap(k/'BUILD.json',v)
seals=J.load(D/'SEALS.json');seals['qd']=reseal(k);J.write(D/'SEALS.json',seals)
pins=J.load(D/'DEPENDENT_PINS.json');pins['qd']['configs']={r:dict(identity=identity(J.load(k/r)),payload_sha256=J.load_raw(k/r)['sha256'],file_sha256=J.sha(k/r)) for r in ('k/c.json','k/n.json')};pins['qd']['proof_mode']='train';J.write(D/'DEPENDENT_PINS.json',pins)
J.write(D/'ARM_BASE_SEALS.json',seals)
print('QD matches N configs; seal',seals['qd'])
