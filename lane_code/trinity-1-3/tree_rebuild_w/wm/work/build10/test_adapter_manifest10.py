from pathlib import Path
import unittest
import torch
from eat1.adapters.build10_manifest import entries
from eat1.artifact import Artifact,write_manifest
from student_pilot.fixed_readout import DepthReadout,HeadingReadout

class AdapterManifest(unittest.TestCase):
    def test_artifact_authenticates_buffers_and_tower_sources(self):
        L=Path(__file__).resolve().parents[2];out=L/'work/merge11/proofs/adapter_manifest/artifact'
        out.mkdir(parents=True,exist_ok=True)
        model=torch.nn.Module();model.auxiliary_heads=torch.nn.Module()
        model.auxiliary_heads.depth_readout=DepthReadout();model.auxiliary_heads.heading=HeadingReadout()
        model.auxiliary_heads.geometry_encoder=torch.nn.Identity()
        torch.save(model.state_dict(),out/'weights.pt')
        files,modules=entries(model,L/'work/tree_r1',out,{'auxiliary_heads.geometry_encoder':dict(role='tower',name='g3t')})
        write_manifest(out/'ARTIFACT.json',out,files,modules)
        artifact=Artifact(out/'ARTIFACT.json');artifact.module_roles(model)
        self.assertEqual(artifact.buffer_offenders,[])
        tower=modules['auxiliary_heads.geometry_encoder']['files']
        self.assertTrue(any(p.endswith('g3t_online.py') for p in tower))
        self.assertTrue(any(p.endswith('utils/rotation.py') for p in tower))
        self.assertTrue(all(files[p]=='tower' and (out/p).is_file() for p in tower))
        self.assertTrue(any(p.endswith('configs/gf1_stage1.json') and role=='config' for p,role in files.items()))

    def test_sandbox_mounts_only_authenticated_external_file(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from eat1.run import run_sandbox
        L=Path(__file__).resolve().parents[2];out=L/'work/merge11/proofs/adapter_manifest/sandbox'
        artifact=SimpleNamespace(root=out/'artifact',path=out/'artifact/ARTIFACT.json',
            files={'../../../../../tree_r1/trace_format/readout_config.json':{'role':'config'}})
        args=SimpleNamespace(code_root=[],items=str(out/'items.jsonl'),sandbox_timeout=1)
        with patch('eat1.run.sandbox_command',return_value=['fixture']) as command,patch('eat1.run.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='fixture')):
            result=run_sandbox(args,[],artifact,[],out)
        binds=command.call_args.args[2]
        expected=str((artifact.root/next(iter(artifact.files))).resolve())
        self.assertIn(expected,binds)
        self.assertNotIn(str(Path(expected).parent),binds)
        self.assertEqual(result['status'],'FAIL')
