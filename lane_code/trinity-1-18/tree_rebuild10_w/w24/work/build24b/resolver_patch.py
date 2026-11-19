from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[2];p=L/'work/build24/joblib.py';a=L/'attic/build24b/joblib.py';assert not a.exists();shutil.copyfile(p,a)
s=p.read_text();at=s.index('def resolve(kit,pool,listing,output):')
s=s[:at]+'''def bound400(spec,milestone,cfg):
    pins=spec.get('m4')
    if cfg.get('r1_training',{}).get('init_policy') is not None and not pins:
        raise ValueError('E74')
    if pins is None:return
    if spec.get('step')!=400:raise ValueError('E75')
    for key,name in (('d','DONE.json'),('e','e.json'),('r','r.json'),('p','RP.json')):
        checked(milestone/name,pins[key])
    with tarfile.open(milestone/'s.tar') as archive:
        raw=archive.extractfile('MANIFEST.json').read()
    if hashlib.sha256(raw).hexdigest()!=pins['v']:raise ValueError('E76')
    receipt=load(milestone/'e.json')
    if receipt['pins']['artifact']['sha256']!=pins['a']:raise ValueError('E77')
    if (cfg['init_artifact']['artifact']!=receipt['pins']['artifact']
            or cfg['r1_training']['p_run']!=load(milestone/'r.json')
            or cfg['r1_training']['handover_receipt']['sha256']!=pins['e']):raise ValueError('E78')


def listing400(spec,pool):
    if not spec.get('m4'):raise ValueError('E74')
    parts=[]
    for i in range(4):
        path=pool_file(pool,Path(spec['n_root'])/'w'/str(i))
        parts.append(dict(name=f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04',pool_path=str(path),bytes=path.stat().st_size))
    return dict(objects=parts,metadata=[])


'''+s[at:]
s=s.replace("    done=load(milestone/'DONE.json')", "    bound400(spec,milestone,load(kit/'k/n.json'))\n    done=load(milestone/'DONE.json')",1)
s=s.replace("listing_value=load(listing);parts=listing_value['objects']", "listing_value=load(listing) if listing is not None else listing400(spec,pool);parts=listing_value['objects']",1)
s=s.replace("    if total!=int(tokens[1]) or combined.hexdigest()!=tokens[2]:raise ValueError('E29')", "    if total!=int(tokens[1]) or combined.hexdigest()!=tokens[2]:raise ValueError('E29')\n    if spec.get('m4') and (total!=spec['m4']['b'] or combined.hexdigest()!=spec['m4']['t']):raise ValueError('E79')",1)
s=s.replace("proof_mode='q',donor_config_sha256=spec['p_runtime_identity'])", "proof_mode=cfg['r1_training'].get('proof_mode','q'),donor_config_sha256=spec['p_runtime_identity'])",1)
s=s.replace("    supplied={entry['sha256']:entry for entry in listing_value.get('metadata',[])}", "    if listing is None:\n        listing_value['metadata']=[dict(name=name,sha256=h,pool_path=str(pool_file(pool,Path(model['root'])/name)),bytes=pool_file(pool,Path(model['root'])/name).stat().st_size)\n            for name,h in model['files'].items() if name.endswith(('.json','.txt','.jinja','.model')) and h not in values]\n    supplied={entry['sha256']:entry for entry in listing_value.get('metadata',[])}",1)
# Model files may live outside the pool behind the established checked alias. Keep the
# same pool_file contract as the original resolver; automatic paths remain in pool.
s=s.replace("pool_file(pool,Path(model['root'])/name)", "pool_file(pool,Path(spec['n_root'])/'u'/h)")
p.write_text(s);compile(s,str(p),'exec')
print('Bound400 authenticates all local control bytes and manifest; export digest remains pinned.')
