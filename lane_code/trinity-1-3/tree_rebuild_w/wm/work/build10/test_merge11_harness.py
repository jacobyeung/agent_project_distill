import json,unittest
from pathlib import Path
import torch
from eat1.artifact import Artifact,write_manifest
from eat1.tests.test_eat1 import FixedMathContract

class ManifestEdges(unittest.TestCase):
    def make(self):return FixedMathContract().make()
    def test_missing_declarations(self):
        for field in ('inputs','buffers'):
            model,art=self.make();data=json.loads(art.path.read_text());data['modules']['math'].pop(field)
            art.path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'requires declared'):Artifact(art.path)
    def test_unregistered_and_nonpersistent(self):
        model,art=self.make();other=torch.nn.Module();object.__setattr__(other,'math',model.math)
        with self.assertRaisesRegex(ValueError,'not registered'):art.module_roles(other)
        model.math.register_buffer('extra',torch.ones(1),persistent=False)
        with self.assertRaisesRegex(ValueError,'every persistent buffer'):art.module_roles(model)
    def test_buffer_binding_authentication(self):
        model,art=self.make();art.modules['math']['buffers']['scale']['file']='absent.pt'
        with self.assertRaisesRegex(ValueError,'not authenticated'):art.module_roles(model)
        model,art=self.make();(art.root/'buffers.pt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'not authenticated'):art.module_roles(model)
    def test_safetensors_binding(self):
        from safetensors.torch import save_file
        model,art=self.make();save_file(model.state_dict(),str(art.root/'buffers.safetensors'))
        modules=art.modules;modules['math']['buffers']['scale']['file']='buffers.safetensors'
        write_manifest(art.path,art.root,{'buffers.safetensors':'head'},modules)
        loaded=Artifact(art.path);loaded.module_roles(model)
        self.assertEqual(loaded.buffer_offenders,[])

    def test_native_adapter_manifest_producers(self):
        import tempfile
        from eat1.adapters.c8r_tiny import make_reader as c8r
        from eat1.adapters.gf1_tiny import make_reader as gf1
        tree=Path(__file__).resolve().parents[2]/'work/tree_r1'
        root=Path(tempfile.mkdtemp(prefix='native_manifest_'))
        for name,maker in (('c8r',c8r),('gf1',gf1)):
            reader=maker(tree=str(tree),workdir=str(root/name))
            artifact=Artifact(reader.artifact_manifest)
            artifact.module_roles(reader.model)
            self.assertEqual(artifact.buffer_offenders,[])
