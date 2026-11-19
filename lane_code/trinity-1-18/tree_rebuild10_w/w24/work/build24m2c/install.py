from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/px.py',(D/'px.py').read_bytes())
 p=k/'b/pl.py';s=p.read_text()
 s=s.replace("    cfg=deepcopy(resolved['config'])", "    from px import resolver\n    need=resolver(kit,root,sources)\n    cfg=deepcopy(resolved['config'])")
 s=s.replace("    for h,p in spec.get('host_paths',{}).items():\n        remember(p,h)\n",'')
 s=s.replace('    def closure(value):', "    def closure(value, field='config.streams'):")
 s=s.replace("if h not in sources:remember(value['path'],h)",'if h not in sources:need(h,field)')
 s=s.replace("for field in ('database','model','division','dense_indices'):\n                                if field in child:closure(child[field])", "for key in ('database','model','division','dense_indices'):\n                                if key in child:closure(child[key],field+'.'+key)")
 s=s.replace("for source in child.get('sources',[]):\n                                for field in ('receipt','model','dense_plan','teacher','clips_plan'):\n                                    if field in source:closure(source[field])", "for i,source in enumerate(child.get('sources',[])):\n                                if not isinstance(source,dict):continue\n                                for key in ('receipt','model','dense_plan','teacher','clips_plan'):\n                                    if key in source:closure(source[key],field+'.sources.'+str(i)+'.'+key)")
 s=s.replace('for v in value.values():closure(v)',"for key,v in value.items():closure(v,field+'.'+str(key))").replace('for v in value:closure(v)',"for i,v in enumerate(value):closure(v,field+'.'+str(i))")
 s=s.replace("closure(cfg['r1_training']['p_run']['config'])", "closure(cfg['r1_training']['p_run']['config'],'config.r1_training.p_run.config')").replace("closure(p_receipt['materialization'])", "closure(p_receipt['materialization'],'P.routing.materialization')").replace('closure(p_config[field])',"closure(p_config[field],'P.config.'+field)").replace('closure(recipe[field])',"closure(recipe[field],'P.materialization.'+field)")
 s=s.replace('if h not in sources:remember(p,h)',"if h not in sources:need(h,'P.materialization.inputs.catalog.'+h)").replace('if h not in sources: remember(p,h)',"if h not in sources:need(h,'config.s1_routing.catalog.'+h)")
 s=s.replace("if h not in sources and h not in paths and Path(p).is_absolute():remember(p,h)","if h not in sources and h not in paths:need(h,'config.pin')")
 a=s.index('    scene=None\n');b=s.index('    cfgraw=',a);s=s[:a]+s[b:]
 a=s.index('    if scene is not None:\n');b=s.index("    entries['e']",a);s=s[:a]+s[b:]
 assert "remember(value['path']" not in s and 'from sc import bind' not in s
 replace(p,s)
 sc=k/'b/sc.py'
 if sc.exists():
  target=L/'attic/build24m2c'/sc.relative_to(L);target.parent.mkdir(parents=True,exist_ok=True);sc.rename(target)
 print(name,reseal(k))
