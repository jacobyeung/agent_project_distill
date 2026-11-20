from common import *
s=(D/'sc.py').read_text().replace("routing_base=None):","routing_base=None,pool_inputs=None):")
s=s.replace("spec=dict(sources=rows,pool_manifest=pool['manifest'],remove_files=cfg['remove_files'],tokenizer=pool.get('tokenizer'))","""original=pool_inputs or pool
        spec=dict(sources=rows,pool_manifest=original['manifest'],remove_files=cfg['remove_files'],tokenizer=original.get('tokenizer'))""")
replace(D/'sc.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/sc.py',s)
 text=(k/'b/pl.py').read_text()
 needle="    cfgpin=write(scratch/'pre.json',cfg)"
 assert needle in text
 text=text.replace(needle,"""    scene_pool_inputs=None
    if not regeneration and cfg.get('r2_all_stream_exclusions'):
        with scope(sources):
            pool_before=load(pinned(cfg['s1_routing']['selection']))
            scene_pool_inputs={key:pool_before.get(key) for key in ('manifest','tokenizer')}
"""+needle)
 text=text.replace("scene=bind(cfg,sources,scratch,q,kit,routing_base=localize(base))","scene=bind(cfg,sources,scratch,q,kit,routing_base=localize(base),pool_inputs=scene_pool_inputs)")
 replace(k/'b/pl.py',text)
 for p in ('BUILD.json','SHA256SUMS.txt'):replace(k/p,(k/p).read_bytes())
 print(name,reseal(k))
