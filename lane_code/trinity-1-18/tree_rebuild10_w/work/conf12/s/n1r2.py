src=open('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/s/n1r.py').read().split("R=W/'tmp/n1r'")[0]
exec(src)
R=W/'tmp/n1r2'
def hf(tag,**kw):return handover_fixture(R/tag,**kw)
both=lambda c,a:(H.progress(c,a)['step'],contract.start(c))
cfg,p,model,art=hf('honest');sc=dict(lm_lr_scale=cfg.get('lm_lr_scale',1.0),pose_lr_scale=cfg.get('pose_lr_scale',1.0))
px={'path':'/x/heads.json','sha256':'f'*64};py={'path':'/y/heads.json','sha256':'f'*64}
c,pp,m,a=hf('eq',scales={'depth_init':px},donor_scales=dict(sc,depth_init=px));rec('equal_depth_pins',lambda:both(c,a))
c,pp,m,a=hf('ne',scales={'depth_init':py},donor_scales=dict(sc,depth_init=px));rec('same_sha_other_path',lambda:both(c,a))
c,pp,m,a=hf('nd',scales={'depth_init':py});rec('N1X_N_depth_init_P_none_remapped',lambda:both(c,a))
import json as j;d=j.load(open(W/'N1R.json'));print('T',d['groups_depth_enabled_true']);print('F',d['groups_depth_enabled_false']);print(d['contract_keys'])
(W/'N1R2.json').write_text(json.dumps(OUT,indent=1,default=str))
