import io
from pathlib import Path
import sys
import tarfile
import unittest
import uuid
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
from adapter import *
from venue import stage_local,extract,packet,FSW,AP

class Venue(unittest.TestCase):
    def setUp(self):
        self.root=B/'work'/('venue_'+uuid.uuid4().hex);self.root.mkdir()
    def archive(self,name,entries):
        p=self.root/name
        with tarfile.open(p,'w') as stream:
            for path,value in entries.items():
                blob=value.encode();member=tarfile.TarInfo(path);member.size=len(blob);member.mode=0o755
                stream.addfile(member,io.BytesIO(blob))
        return pin(p)
    def test_staging_allowlist_and_pins(self):
        metadata=self.archive('a.tar',{'fsw/a/config.json':'{}','sj/forbidden/cohort.json':'{}'})
        model=self.archive('b.tar',{'fsw/b/manifest.json':'{}'})
        runtime=self.archive('c.tar',{'rwtrain_torch211_cu129/bin/python3.12':'fixture'})
        fla=self.archive('d.tar',{'ebe69df8/p/site/module.py':'pass\n'})
        import hashlib
        manifest=self.root/'m.sha';manifest.write_text(hashlib.sha256(b'pass\n').hexdigest()+' site/module.py\n')
        assets=dict(metadata_archive=metadata,model_archive=model,runtime_archive=runtime,fla_archive=fla,
            fla_manifest=pin(manifest),runtime_relative_root='rwtrain_torch211_cu129',
            base_bindings=[],export_logical=FSW+'/export',export_root=str(self.root/'export'))
        result=stage_local(self.root/'staged',assets,100000)
        self.assertFalse((self.root/'staged/metadata/sj').exists())
        self.assertEqual((Path(result['fla_root'])/'site/module.py').read_text(),'pass\n')
        self.assertIn((str(self.root/'staged/metadata/fsw'),FSW),result['base_bindings'])
    def test_allocation_family_admission(self):
        from copy import deepcopy
        from orchard import admit
        family=load(B/'out/FAMILY.json');inputs=self.root/'input';inputs.mkdir()
        dump(inputs/'BOUND.json',dict(source_sha256=family['inputs']['item_sha256'],media_sha256=family['inputs']['media_sha256'],synthetic=False))
        self.assertFalse(admit(family,dict(inputs=str(inputs)))['synthetic'])
        bad=deepcopy(family);bad['protocol']['served'].append('ground')
        with self.assertRaisesRegex(ValueError,'protocol'):admit(bad,dict(inputs=str(inputs)))
        bad=deepcopy(family);bad['code_sources']['engine.py']='0'*64
        with self.assertRaisesRegex(ValueError,'code differs'):admit(bad,dict(inputs=str(inputs)))
    def test_unsafe_archive(self):
        value=self.archive('bad.tar',{'../escape':'x'})
        with self.assertRaisesRegex(ValueError,'escapes'):extract(value['path'],self.root/'out',10000)
    def test_budget(self):
        value=self.archive('large.tar',{'a':'0123456789'})
        with self.assertRaisesRegex(ValueError,'allowance'):extract(value['path'],self.root/'out',1)
    def test_packet_limit_and_directives(self):
        family=self.root/'FAMILY.json';assets=self.root/'ASSETS.json'
        dump(family,dict(limits=dict(full=dict(gpu_seconds=21600)),blockers=['fixture']));dump(assets,{})
        packet(family,assets,self.root/'packet','3917ab0dd64f429ac1e708fb')
        script=(self.root/'packet/BATCH.sh').read_text()
        self.assertLess(script.index('#SBATCH'),script.index('set -e'))
        self.assertIn('orchard.py',script)
        self.assertFalse(load(self.root/'packet/PACKET.json')['ready'])
    def test_historical_proof_staging_is_isolated(self):
        from proof_stage import prepare
        from venue import SJ
        code=self.archive('code_c8r.tar',{'sj/orch_cd/evalx/work/milestone/native/out2/original.py':'pass\n'})
        self.archive('metadata_e10fbb95487f3baf.tar',{'fsw/config.json':'{}','sj/cohort.json':'{}'})
        self.archive('geometry_8c58df1547371bdb.tar',{'sj/raw/a.npz':'fixture'})
        self.archive('masks_4984fac22d84e8c5.tar',{'sj/masks/a.npz':'fixture'})
        self.archive('frames.tar',{'ab/f.png':'fixture'})
        returned=self.archive('returned.tar',{'native/geometry/GEOMETRY_MANIFEST.json':'{}','native/R1.json':'{}'})
        assets=self.root/'ASSETS.json';family=self.root/'FAMILY.json';reference=self.root/'REFERENCE.json';request=self.root/'REQUEST.json'
        dump(assets,dict(base_bindings=[],export_root=str(self.root/'export'),export_logical=FSW+'/export',tree_logical=SJ+'/tree'))
        dump(family,{});dump(reference,[])
        dump(request,dict(frames_root=SJ+'/frames',grounding=dict(geometry_manifest=dict(path=SJ+'/run/native/geometry/GEOMETRY_MANIFEST.json')),config={},artifact={},data_receipt={}))
        result=prepare(self.root/'proof',assets,family,code['path'],self.root,reference,request,returned['path'])
        staged=self.root/'proof/original/sj'
        self.assertEqual((staged/'frames/ab/f.png').read_text(),'fixture')
        self.assertTrue((staged/'run/native/geometry/GEOMETRY_MANIFEST.json').is_file())
        self.assertFalse((staged/'run/native/R1.json').exists())
        self.assertIn((str(staged),SJ),result['base_bindings'])
        self.assertEqual(load(Path(result['inputs'])/'SPEC.json')['proof_core'],SJ+'/orch_cd/evalx/work/milestone')
if __name__=='__main__':unittest.main(verbosity=2)
