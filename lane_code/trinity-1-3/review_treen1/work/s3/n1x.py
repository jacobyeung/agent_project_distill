src=open('/scratch/jjyeung/orch_n30/review_treen1/work/s3/n1.py').read().split("R=W/")[0]
exec(src)
R=W/'tmp/n1x'
dpin=dict(path=str(T/'student_pilot/r2_dev_merged.json'),sha256='d'*64)
# N has depth_init (as in the r1 kit), P lacks it -> encoder_copy frozen in N, trained in P
c,p_,a,r=make(R/'depth',ntweak=lambda c:c.update(depth_init=dpin))
OUT['N_has_depth_init']=c.get('depth_init') is not None;OUT['P_has_depth_init']=p_.get('depth_init') is not None
rec('N1a_P_without_depth_init_vs_N_with',lambda:contract.start(mapping(c,a,r)))
# P initialised from a C1-r artifact with head_init (inherited trunk tensors at LM rate); N inits from P export
c2,p2,a2,r2=make(R/'inh',ptweak=lambda p:p.update(init_artifact={'artifact':{'path':'c1r/artifact.json','sha256':'e'*64},'heads':['pose','depth'],'lm':'full'}))
rec('N1a_P_init_c1r_head_init_vs_N',lambda:contract.start(mapping(c2,a2,r2)))
OUT['note']='depth_init freezes depth.model.visual (carrier_c1.py:720) so encoder_copy has no trainable group; head_init moves inherited pose tensors to heads_pretrained at lm_learning_rate (carrier_c1_run.py:1004-1010, carrier_c1.py:626ff). Neither input is in optimizer_contract.'
(W/'N1X.json').write_text(json.dumps(OUT,indent=1,default=str))
