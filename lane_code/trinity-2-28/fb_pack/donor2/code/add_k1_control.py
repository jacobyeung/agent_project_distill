from pathlib import Path
p=Path(__file__).resolve().parent/'k1_fixture.py';s=p.read_text();s=s.replace('import copy,hashlib,json,os,sys,types,tempfile','import copy,hashlib,json,os,sys,types,tempfile\nfrom unittest import mock')
pos=" epin=native_export(model,root/'export')"
extra=''' epin=native_export(model,root/'export')
 control=[]
 if variant=='V1':
  depth=model.auxiliary_heads.depth
  original=donor.point_depth.encode
  probe=torch.zeros(1,32,depth.fov.in_features)
  def leaky(grid,vits,fov):
   live=(1e-4+(np.pi-2e-4)*depth.fov(probe).sigmoid())[0].detach()
   return original(grid,vits,live)
  for c,(batch,state) in zip(selection['captures'],pairs):
   good=donor(batch,state).clone()
   with torch.no_grad():depth.fov.bias.sub_(.5)
   assert torch.equal(good,donor(batch,state))
   with mock.patch.object(donor.point_depth,'encode',side_effect=leaky):
    bad0=donor(batch,state).clone()
    with torch.no_grad():depth.fov.bias.sub_(.5)
    bad1=donor(batch,state).clone()
    try:
     assert torch.equal(bad0,bad1),'live FoV leak'
    except AssertionError:
     refused=True
    else:
     raise AssertionError('Negative control escaped invariance check')
   control.append(dict(canonical=c['canonical'],correct_donor_invariant=True,leaky_v1_status='FAIL',invariance_assertion_caught=refused,before_sha256=array_hash(bad0),after_sha256=array_hash(bad1)))
'''
assert pos in s;s=s.replace(pos,extra);s=s.replace("reports.append(dict(variant=variant,settings=cfg", "reports.append(dict(variant=variant,negative_control=control,settings=cfg");p.write_text(s)
