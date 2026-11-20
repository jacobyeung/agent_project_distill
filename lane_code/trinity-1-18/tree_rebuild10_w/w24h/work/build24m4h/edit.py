import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
k=kit('n');changes={'rb.py':(D/'rb.py').read_text()}
s=(k/'b/rg.py').read_text();s=s.replace('    result=build(cfg', '    from rb import routing_status\n    routing_status(cfg)\n    result=build(cfg')
a=s.index('        from copy import deepcopy');b=s.index('        hashes=',a)
s=s[:a]+'''        from rb import reconstruct, DB
        p_pin=cfg['r1_training']['p_run']['config'];p=load(pinned(p_pin));pin=p['streams']['routing']
        receipt=load(pinned(pin));p_db=pinned(receipt['database'])
        if receipt['database']['sha256']!=DB:raise ValueError('P_TRAINED_ROUTING_DATABASE_DIFFERS')
        rebuilt=reconstruct(cfg,root,directory='pr')
        reproduced=load(root/'pr/receipt.json')
'''+s[b:];changes['rg.py']=s
s=(k/'b/i.py').read_text();s=s.replace('    if not spec:return request', '    if not spec:return request\n    from rb import routing_status')
s=s.replace("if original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):return request", "if original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):\n        routing_status(cfg)\n        return request")
s=s.replace("    spec['selection']=file_pin(root/'s/receipt.json')", "    spec['selection']=file_pin(root/'s/receipt.json')\n    routing_status(cfg)")
changes['i.py']=s
s=(k/'b/z.py').read_text();s=s.replace("cfg['s1_routing']=runtime['s1_routing']", "cfg['s1_routing']=load(kit/'k/n.json')['s1_routing']")
changes['z.py']=s
s=(k/'b/pl.py').read_text();s=s.replace("        for field in ('remove_files','dev_scene_exclusions','benchmark_scene_exclusions'):","        closure(p_config['code'],'P.config.code')\n        for field in ('remove_files','dev_scene_exclusions','benchmark_scene_exclusions'):")
changes['pl.py']=s
s=(k/'b/a.py').read_text();s=s.replace('original_host = host_entry.frame_host', '''original_selection = host_entry.check_host_selection
def guarded_selection(cfg, *args, **kwargs):
 from rb import routing_status
 routing_status(cfg)
 return original_selection(cfg, *args, **kwargs)
host_entry.check_host_selection = guarded_selection
original_host = host_entry.frame_host''')
changes['a.py']=s
for n in NAMES:
 for name,s in changes.items():replace(kit(n)/'b'/name,s)
J.write(D/'CHANGED_B.json',list(changes))
print('EDITED',list(changes))
