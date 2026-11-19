import json,sys,hashlib
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/work/tree_r1';sys.path.insert(0,T)
from student_pilot import r1_handover as H, carrier_c1_run as C
want='620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a'
for f in ['/scratch/jjyeung/orch_n30/tree_rebuild_w/work/cont_real/m100/x_69d2930d/k/666c05ea.json','/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json','/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4/cert_p4_hz_a71_3/b/config.json','/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4/cert_p4_hz_a71_3/b/c.json']:
    try:
        c=json.load(open(f))
        if 'payload' in c:
            import base64;c=json.loads(base64.b64decode(c['payload']))
        e=H.export_identity(c); i=C.identity(c)
        print(f[-45:], 'export_identity',e[:12], 'identity',i[:12], 'MATCH' if want in (e,i) else '-')
    except Exception as x: print(f[-45:],'ERR',type(x).__name__,str(x)[:120])
