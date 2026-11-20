from pathlib import Path
"""Real-byte resolver regressions; only unavailable payloads use explicit stand-ins."""
from pathlib import Path
from copy import deepcopy
from contextlib import contextmanager
from unittest.mock import patch
import hashlib,importlib.util,io,json,sys,tarfile,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';E=L.parent/'ext/m400real';K=B/'kits/q'
if not E.exists():E=D/'inputs/m400real'
if not E.exists():E=L/'work/build24b/inputs/m400real'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24o/work/tree_r1c']
import joblib as J
from launch_r2.build import capsule_json
from student_pilot.r1_handover import export_identity

def old_module():
    spec=importlib.util.spec_from_file_location('old_joblib21e',L/'attic/build21e/joblib.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def archive(path,files):
    with tarfile.open(path,'w') as t:
        for name,raw in files.items():
            item=tarfile.TarInfo(name);item.size=len(raw);t.addfile(item,io.BytesIO(raw))

def fixture():
    root=D/'proofs/real';root.mkdir(parents=True,exist_ok=True)
    spec=J.load(K/'k/p.json');pool=root/'pool';m=pool/spec['milestone'];m.mkdir(parents=True,exist_ok=True)
    manifest=deepcopy(J.load(E/'MANIFEST.json'));files={};standins=[];real=[]
    for item in manifest['files']:
        name='files'+item['path'];p=E/name
        if p.is_file():
            raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
            real.append(dict(path=name,bytes=len(raw),sha256=item['sha256']))
        else:
            raw=b'{}\n' if name.endswith('.json') else ('fixture:'+name+'\n').encode()
            standins.append(dict(path=name,original_sha256=item['sha256'],original_bytes=item['bytes']))
            item.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),pin=hashlib.sha256(raw).hexdigest(),match=True)
        files[name]=raw
    archive(m/'s.tar',{'MANIFEST.json':json.dumps(manifest).encode(),**files})
    for name in ('e.json','r.json','DONE.json','RP.json'):(m/name).write_bytes((E/name).read_bytes())
    parts=[];combined=b'fixture export payload, not production weights\n'
    for i in range(4):
        raw=combined[len(combined)*i//4:len(combined)*(i+1)//4];p=pool/f'p{i}';p.write_bytes(raw)
        parts.append(dict(name=f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04',pool_path=str(p),bytes=len(raw)))
    marker=pool/spec['p_root']/'o/gcs_6ed2c7aa_m400.done';marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(f'q8/8865619b/6ed2c7aa_m400.tar {len(combined)} {hashlib.sha256(combined).hexdigest()}\n')
    values,metadata=J.small_archive(m/'s.tar')
    receipt=J.load(E/'e.json');prep=metadata[receipt['pins']['preparation']['sha256']];model=metadata[prep['model']['sha256']]
    external=[]
    for i,(name,h) in enumerate(model['files'].items()):
        if name.endswith(('.json','.txt','.jinja','.model')) and h not in values:
            p=pool/f'm{i}';p.write_bytes(b'{}\n' if name.endswith('.json') else b'fixture\n')
            external.append(dict(name=name,sha256=h,pool_path=str(p),bytes=p.stat().st_size))
    listing=root/'listing.json';J.write(listing,dict(objects=parts,metadata=external))
    J.write(D/'FIXTURE.json',dict(real=real,standins=standins,external_metadata=external,
        note='All available real member bytes and real e/r/DONE/RP are unchanged. Missing members use tiny placeholders with rewritten manifest hashes/lengths. Export parts and their marker use fixture bytes. External model metadata bytes are unavailable; only their checked() boundary is substituted in resolver PASS tests, never the receipt/config/binding/preparation hashes or identities.'))
    return dict(root=root,pool=pool,m=m,listing=listing,spec=spec,values=values,metadata=metadata,files=files,manifest=manifest,external=external)

@contextmanager
def external_boundary(f,module=J):
    checked=module.checked;allowed={x['pool_path']:x for x in f['external']}
    def check(path,expected,size=None):
        if str(path) in allowed:
            entry=allowed[str(path)];assert expected==entry['sha256'] and size==entry['bytes']
            return Path(path)
        return checked(path,expected,size)
    with patch.object(module,'checked',check):yield

class Resolver21e(unittest.TestCase):
    controls=[]
    @classmethod
    def setUpClass(cls):cls.f=fixture()

    def test_old_jsonl_exact_failure(self):
        old=old_module()
        with self.assertRaisesRegex(json.JSONDecodeError,'Extra data: line 2 column 1') as c:old.small_archive(self.f['m']/'s.tar')
        self.controls.append(dict(test=self.id(),old=str(c.exception),new='PASS: hash-verified values'))
        for name,size in (('n.json',107499),('z.json',2982924)):
            value=next(v for v in self.f['values'].values() if v['original'].endswith('/69d2930d/'+name))
            self.assertEqual(value['bytes'],size);self.assertNotIn(value['sha256'],self.f['metadata'])

    def test_old_identity_exact_failure(self):
        old=old_module();load=old.load
        spec=deepcopy(self.f['spec']);spec['p_identity']=spec['p_kit_identity']
        with patch.object(old,'load',side_effect=lambda p:spec if Path(p)==K/'k/p.json' else load(p)),patch.object(old,'small_archive',J.small_archive):
            with self.assertRaisesRegex(ValueError,'^E23$') as c:old.resolve(K,self.f['pool'],self.f['listing'],self.f['root']/'old.json')
        self.controls.append(dict(test=self.id(),old=str(c.exception),new='PASS: runtime identity'))

    def test_resolve_real_metadata(self):
        with external_boundary(self.f):result=J.resolve(K,self.f['pool'],self.f['listing'],self.f['root']/'resolved.json')
        self.assertEqual(result['config']['r1_training']['donor_config_sha256'],self.f['spec']['p_runtime_identity'])
        self.assertEqual(result['config']['r1_training']['p_run'],J.load(E/'r.json'))
        # The omitted archive tokenizer adds one stand-in to the eight production external files.
        self.assertEqual(len(result['external_metadata']),9)
        self.assertEqual(result['config']['r2_identity']['init']['step'],544)

    def test_pinned_jsonl_refuses_by_name(self):
        pins=J.load(E/'e.json')['pins']
        for label in ('artifact','config','binding','preparation','full_weights'):
            metadata=deepcopy(self.f['metadata']);pin=pins[label];metadata.pop(pin['sha256'])
            raw=self.f['files']['files'+pin['path']]+b'\n{}\n'
            h=hashlib.sha256(raw).hexdigest();values=dict(self.f['values']);values[h]=dict(member='files'+pin['path'])
            bad=dict(pin,sha256=h)
            with self.subTest(label=label),self.assertRaisesRegex(ValueError,'E50:.*'+Path(pin['path']).name) as c:
                J.metadata_closure(values,metadata,[bad])
            self.controls.append(dict(test=self.id(),label=label,error=str(c.exception)))

    def test_model_manifest_and_other_metadata_jsonl(self):
        for pin in (self.f['metadata'][J.load(E/'r.json')['preparation']['sha256']]['model'],
                    J.load(E/'e.json')['pins']['stream/routing']):
            metadata=dict(self.f['metadata']);metadata.pop(pin['sha256'])
            with self.assertRaisesRegex(ValueError,'E50:.*'+Path(pin['path']).name):J.metadata_closure(self.f['values'],metadata,[pin])

    def test_artifact_identity_refuses(self):
        receipt=J.load(E/'e.json');run=J.load(E/'r.json')
        for h in ('0'*64,self.f['spec']['p_kit_identity']):
            metadata=deepcopy(self.f['metadata']);metadata[receipt['pins']['artifact']['sha256']]['config_sha256']=h
            with self.assertRaisesRegex(ValueError,'^E23$'):J.identities(self.f['spec'],run,receipt['pins'],self.f['values'],metadata)

    def test_identity_relations_refuse(self):
        pins=J.load(E/'e.json')['pins'];run=J.load(E/'r.json')
        for key in ('p_runtime_identity','p_kit_identity','p_run'):
            spec=deepcopy(self.f['spec']);spec[key]='0'*64 if key!='p_run' else {}
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'E(23|51|52)'):J.identities(spec,run,pins,self.f['values'],self.f['metadata'])
        for label in ('binding','preparation'):
            meta=deepcopy(self.f['metadata']);meta[pins[label]['sha256']]['config_sha256']=self.f['spec']['p_kit_identity']
            with self.subTest(label=label),self.assertRaisesRegex(ValueError,'E25'):J.identities(self.f['spec'],run,pins,self.f['values'],meta)

    def test_identity_algorithm_matches_tree(self):
        for label in ('config',):
            v=self.f['metadata'][J.load(E/'r.json')[label]['sha256']]
            self.assertEqual(J.export_identity(v),export_identity(v))
        v=self.f['metadata'][self.f['spec']['p_kit_config']['sha256']]
        self.assertEqual(J.export_identity(v),export_identity(v))

    def test_real_bytes_metadata_mutation(self):
        pin=J.load(E/'r.json')['config'];files=dict(self.f['files']);name='files'+pin['path']
        files[name]+=b'\n{}\n';manifest=deepcopy(self.f['manifest']);h=hashlib.sha256(files[name]).hexdigest()
        item=next(x for x in manifest['files'] if x['path']==pin['path'])
        item.update(bytes=len(files[name]),sha256=h,pin=h)
        path=self.f['root']/'mutated.tar'
        archive(path,{'MANIFEST.json':json.dumps(manifest).encode(),**files})
        values,metadata=J.small_archive(path)
        with self.assertRaisesRegex(ValueError,'E50:.*config.json') as c:J.metadata_at(values,metadata,dict(pin,sha256=h))
        self.controls.append(dict(test=self.id(),error=str(c.exception),mutation='Real config bytes followed by a second JSON document; archive manifest repinned.'))

    def test_relation_and_stream_mutations(self):
        pins=J.load(E/'e.json')['pins'];run=J.load(E/'r.json');spec=deepcopy(self.f['spec'])
        meta=deepcopy(self.f['metadata']);meta[pins['config']['sha256']]['output']='/changed'
        identity=J.export_identity(meta[pins['config']['sha256']]);spec['p_runtime_identity']=identity
        for label in ('artifact','binding','preparation'):meta[pins[label]['sha256']]['config_sha256']=identity
        with self.assertRaisesRegex(ValueError,'E53'):J.identities(spec,run,pins,self.f['values'],meta)
        meta=deepcopy(self.f['metadata']);meta[pins['preparation']['sha256']]['streams']['routing']['receipt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'E54'):J.identities(self.f['spec'],run,pins,self.f['values'],meta)

    def test_data_role_does_not_exempt_metadata_role(self):
        pin=next(dict(path=v['original'],sha256=h) for h,v in self.f['values'].items() if v['original'].endswith('/69d2930d/n.json'))
        J.metadata_closure(self.f['values'],self.f['metadata'],[dict(remove_files=[pin])])
        with self.assertRaisesRegex(ValueError,'E50:.*n.json'):
            J.metadata_closure(self.f['values'],self.f['metadata'],[dict(remove_files=[pin],model=pin)])

    def test_hash_checks_survive_jsonl(self):
        files=dict(self.f['files']);name=next(n for n in files if n.endswith('/69d2930d/n.json'))
        files[name]=b'X'+files[name][1:]
        path=self.f['root']/'mutated.tar';archive(path,{'MANIFEST.json':json.dumps(self.f['manifest']).encode(),**files})
        with self.assertRaisesRegex(ValueError,'E17'):J.small_archive(path)

    def test_manifest_and_input_jsonl_refuse_by_name(self):
        path=self.f['root']/'mutated.tar';archive(path,{'MANIFEST.json':b'{}\n{}\n'})
        with self.assertRaisesRegex(ValueError,'E50:MANIFEST.json'):J.small_archive(path)
        path=self.f['root']/'invalid.json';path.write_bytes(b'{}\n{}\n')
        with self.assertRaisesRegex(ValueError,'E50:.*invalid.json'):J.load(path)

    def test_external_metadata_missing_refuses(self):
        load=J.load
        with patch.object(J,'load',side_effect=lambda p:dict(objects=load(p)['objects']) if Path(p)==self.f['listing'] else load(p)):
            with self.assertRaisesRegex(ValueError,'E41:'):J.resolve(K,self.f['pool'],self.f['listing'],self.f['root']/'missing.json')

    def test_external_metadata_jsonl_refuses_by_name(self):
        f=deepcopy(self.f);entry=next(x for x in f['external'] if x['name'].endswith('.json'))
        path=Path(entry['pool_path']);saved=path.read_bytes();listing=J.load(f['listing']);load=J.load
        path.write_bytes(b'{}\n{}\n');entry['bytes']=path.stat().st_size
        listing['metadata']=f['external']
        try:
            with external_boundary(f),patch.object(J,'load',side_effect=lambda p:listing if Path(p)==f['listing'] else load(p)):
                with self.assertRaisesRegex(ValueError,'E50:'+entry['name']):J.resolve(K,f['pool'],f['listing'],f['root']/'bad_external.json')
        finally:path.write_bytes(saved)

    @classmethod
    def tearDownClass(cls):
        if cls.controls:J.write(D/'MUTATIONS.json',cls.controls)
