"""Install the remaining host integrations after the baseline suite finishes."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]
T=L/'work/tree_r1'
if (T/'launch_r2/runtime.py').exists():
    raise ValueError('Runtime already installed; use the sealed tree rather than repeating this one-time edit')
(T/'launch_r2/runtime.py').write_bytes((L/'work/build3/runtime_source.py').read_bytes())
p=T/'student_pilot/carrier_c1_run.py'
s=p.read_text()
old='''    if encode_only:
        recipe = recipe_for(cfg)
        counts = {k:v['count'] for k,v in receipt['streams'].items()}
        offset = cfg.get('row_start_step', 0)
        plan = next(data.mixed_indices(counts,offset+1,start_step=offset,training_mode=cfg.get('training_mode', 'mixed'),
                                     mix=recipe['mix'],world=recipe['world_size'],r2_sampling=cfg.get('r2_sampling')))
        return encode_plan_rows(receipt, processor, [plan], list(range(recipe['world_size'])), report_path)
'''
new='''    recipe = recipe_for(cfg)
    counts = {k:v['count'] for k,v in receipt['streams'].items()}
    offset = cfg.get('row_start_step', 0)
    plan = next(data.mixed_indices(counts,offset+1,start_step=offset,training_mode=cfg.get('training_mode', 'mixed'),
                                 mix=recipe['mix'],world=recipe['world_size'],r2_sampling=cfg.get('r2_sampling')))
    if encode_only:
        return encode_plan_rows(receipt, processor, [plan], list(range(recipe['world_size'])), report_path)
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''    counts = {k:v['count'] for k,v in receipt['streams'].items()}
    recipe = recipe_for(cfg)
    offset = cfg.get('row_start_step', 0)
    plan = next(data.mixed_indices(counts,offset+1,start_step=offset,training_mode=cfg.get('training_mode', 'mixed'),
                                   mix=recipe['mix'],world=recipe['world_size'],r2_sampling=cfg.get('r2_sampling')))
'''
assert s.count(old)==1
s=s.replace(old,'')
p.write_text(s)
p=T/'tests/test_r2_build3.py';s=p.read_text()
s=s.replace("        module=importlib.import_module(entry['file'][:-3].replace('/','.'))\n", "        with self.assertRaisesRegex(ValueError,'bank adapter'):\n            invoke(entry)\n    return test\n\n\ndef invoke(entry):\n        module=importlib.import_module(entry['file'][:-3].replace('/','.'))\n")
s=s.replace("        with self.assertRaisesRegex(ValueError,'bank adapter'):function(**args)\n    return test\n", "        function(**args)\n")
p.write_text(s)
