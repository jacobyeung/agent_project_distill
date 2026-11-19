"""C1 import closure and source-seal regressions; all fixtures stay on scratch."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import carrier_c1_run as run, p3_provenance as provenance


class ProvenanceTests(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix='closure_',dir=os.environ['LANE_TEST_OUTPUT']))

    def test_explicit_entrypoint_includes_only_reachable_local_modules(self):
        root=self.root()
        sources={
            'student_pilot/__init__.py':'',
            'student_pilot/p3_provenance.py':'',
            'student_pilot/p3_unrelated.py':'raise RuntimeError("unrelated")',
            'student_pilot/entry.py':'from . import leaf\nfrom .pkg import child\nimport headcall.geometry\n',
            'student_pilot/leaf.py':'from . import p3_provenance\n',
            'student_pilot/pkg/__init__.py':'from . import extra\n',
            'student_pilot/pkg/child.py':'',
            'student_pilot/pkg/extra.py':'',
            'headcall/__init__.py':'',
            'headcall/geometry.py':''}
        for name,raw in sources.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(raw)
        with patch.object(provenance,'__file__',str(root/'student_pilot/p3_provenance.py')):
            actual=provenance.source_files([root/'student_pilot/entry.py'])
        self.assertEqual({str(p.relative_to(root)) for p in actual},set(sources)-{'student_pilot/p3_unrelated.py'})

    def test_actual_runtime_imports_and_lazy_readout_sources_are_sealed(self):
        root=Path(run.__file__).resolve().parent.parent
        closure=provenance.source_files([Path(run.__file__)])
        names={str(p.relative_to(root)) for p in closure}
        self.assertNotIn('official/score_and_aggregate.py',names)
        self.assertNotIn('student_pilot/p3_kit.py',names)
        for name in ('student_pilot/carrier_c1_clip.py','student_pilot/all_frame_readout.py',
                     'student_pilot/decoupled_resume.py','student_pilot/p3_provenance.py','headcall/geometry.py'):
            self.assertIn(name,names)
        program='''import json,sys
from pathlib import Path
from student_pilot import carrier_c1_run
root=Path(carrier_c1_run.__file__).resolve().parent.parent
print(json.dumps(sorted({str(Path(m.__file__).resolve().relative_to(root)) for m in list(sys.modules.values())
 if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(root)})))
'''
        result=subprocess.run([sys.executable,'-B','-c',program],cwd=root,check=True,capture_output=True,text=True)
        self.assertLessEqual(set(json.loads(result.stdout)),names)
        out=self.root();seal=dict(schema='c1-clean-source-v1',clean=True,commit='1'*40,
                                sources={str(p.relative_to(root)):provenance.sha256(p) for p in closure})
        provenance.write(out/'seal.json',seal)
        cfg={'code':provenance.file_pin(out/'seal.json')}
        self.assertEqual(run.authenticate(cfg),'1'*40)
        for index,change in enumerate(({'clean':False},{'commit':'1'},
                {'sources':{**seal['sources'],'student_pilot/carrier_c1_clip.py':'0'*64}},
                {'sources':{k:v for k,v in seal['sources'].items() if k!='headcall/geometry.py'}})):
            path=out/f'bad{index}.json';provenance.write(path,{**seal,**change})
            with self.assertRaisesRegex(ValueError,'exact committed'):
                run.authenticate({'code':provenance.file_pin(path)})


if __name__=='__main__':unittest.main()
