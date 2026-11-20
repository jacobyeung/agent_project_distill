from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name);s=(k/'b/pl.py').read_text()
 s=s.replace('from cs import sources as census_sources,preflight','from cs import sources as census_sources,preflight,discovery')
 s=s.replace("            preflight(kit,root.parent,effective,source_record,os.environ['SLURM_JOB_ID'])","            if discovery(kit):preflight(kit,root.parent,effective,source_record,os.environ['SLURM_JOB_ID'])")
 replace(k/'b/pl.py',s)
s=(D/'cs.py').read_text()
s=s.replace("    root=Path(root);source=load(root/'p/q/ss.json')",'''    from z import checked
    root=Path(root)
    host=load(root/'p/q/host.json')
    h=host.get('staging_plan_sha256')
    if not isinstance(h,str) or len(h)!=64:raise ValueError('R1_CENSUS_SOURCE_MANIFEST_MISSING')
    manifest=load(checked(root/'p/i/staging.json',h))
    entry=manifest.get('entries',{}).get('ss.json')
    if not isinstance(entry,dict):raise ValueError('R1_CENSUS_SOURCE_MANIFEST_MISSING')
    source=load(checked(root/'p/q/ss.json',entry['sha256'],entry['bytes']))''')
replace(D/'cs.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/cs.py',s)
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
