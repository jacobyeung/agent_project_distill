from pathlib import Path
import ast,shutil,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
import joblib as J
from kit import reseal
p=B/'joblib.py';s=p.read_text()
s=s.replace("    return dict(objects=parts,metadata=[])", "    path=pool_file(pool,Path(spec['n_root'])/'l.json')\n    metadata=load(path).get('metadata',[]) if path.is_file() else []\n    return dict(objects=parts,metadata=metadata)",1)
s=s.replace("    if listing is None:\n        listing_value['metadata']", "    if listing is None and not listing_value.get('metadata'):\n        listing_value['metadata']",1)
s=s.replace("pool_file(pool,Path(spec['n_root'])/'u'/h)", "pool_file(pool,Path(pool)/'m'/h)")
p.write_text(s)
# Every supported build24 regeneration selects the m400 kit builder.
p=B/'kit.py';save=L/'attic/build24b/kit_generator.py';assert not save.exists();shutil.copyfile(p,save);s=p.read_text();node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');lines=s.splitlines(True)
replacement='''def main():
    import importlib.util
    path=L/'work/build24b/kit.py'
    spec=importlib.util.spec_from_file_location('kit24b_generator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.main()
'''
p.write_text(''.join(lines[:node.lineno-1])+replacement+''.join(lines[node.end_lineno:]))
# Regeneration starts from retained templates; repeated runs preserve superseded kits.
p=D/'kit.py';s=p.read_text();s=s.replace("  if not save.exists():shutil.copytree(k,save)\n", "  if not save.exists():shutil.copytree(k,save)\n  else:\n   import time\n   k.rename(A/(name+'_superseded_'+str(time.time_ns())))\n   shutil.copytree(save,k)\n")
s=s.replace("  old.rename(A/(name+'_'+old.name))", "  import time\n  old.rename(A/(name+'_'+str(time.time_ns())+'_'+old.name))")
p.write_text(s)
records=J.load(D/'KIT.json')
for name in ('q','n'):
 k=B/'kits'/name;(k/'b/z.py').write_bytes((B/'joblib.py').read_bytes());seal=reseal(k);records[name]['kit_seal']=seal
 doc=J.load(D/('UPLOADS_'+name+'.json'))
 for item in doc['files']:
  if item['opaque_name'].startswith(name+'/'):
   p=Path(item['local_path']);item.update(sha256=J.sha(p),bytes=p.stat().st_size)
 doc['total_bytes']=sum(x['bytes'] for x in doc['files']);J.write(D/('UPLOADS_'+name+'.json'),doc)
J.write(D/'KIT.json',records)
print(json.dumps(records,indent=2))
