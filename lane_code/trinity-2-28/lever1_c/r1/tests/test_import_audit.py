"""Fail on missing sealed imports, including deferred and dynamic GPU imports."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import json
import unittest
import import_audit as A

class ImportAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(HERE/'out/delivery.tgz').read_bytes()
        cls.files=A.unpack(A.unpack(cls.raw)['0.tgz'])
        cls.result=A.audit(cls.raw)
        (HERE/'out/IMPORT_AUDIT.json').write_text(json.dumps(cls.result,indent=2)+'\n')

    def test_exact_delivery_import_closure(self):
        self.assertTrue(self.result['passed'], self.result['unresolved'])
        self.assertEqual(self.result['retained_sources'],296)
        self.assertEqual(self.result['vendor_files'],26)
        self.assertEqual(self.result['files_parsed'],342)
        self.assertTrue(any(r['scope'] for r in self.result['edges']))
        self.assertTrue(any(r['kind']=='literal_dynamic' for r in self.result['edges']))
        self.assertTrue(any('embedded_sha256' in r for r in self.result['edges']))
        self.assertTrue(all(r['reason'] for r in self.result['excluded']))

    def test_missing_vendor_file_fails(self):
        info=json.loads((HERE/'out/BUILD.json').read_text())
        path=info['layout']['paths']['tree/student_pilot/g3t_vendor/vggt/utils/load_fn.py']
        result=A.audit(self.raw,{path:None})
        self.assertFalse(result['passed']);self.assertTrue(result['unresolved'])

    def test_new_deferred_import_fails(self):
        result=A.audit(self.raw,{'g/w.py':self.files['g/w.py']+b'\ndef later():\n    import absent_gpu_dependency\n'})
        self.assertFalse(result['passed'])
        self.assertTrue(any(r.get('name')=='absent_gpu_dependency' for r in result['unresolved']))

    def test_literal_dynamic_imports_and_aliases_fail(self):
        code=b'\ndef later():\n    import importlib as il\n    from importlib import import_module as im\n    il.import_module("absent_dynamic_one")\n    im("absent_dynamic_two")\n    __import__("absent_dynamic_three")\n'
        result=A.audit(self.raw,{'g/w.py':self.files['g/w.py']+code})
        names={r.get('name') for r in result['unresolved']}
        self.assertTrue({'absent_dynamic_one','absent_dynamic_two','absent_dynamic_three'}<=names)

    def test_missing_from_import_fails(self):
        result=A.audit(self.raw,{'g/w.py':self.files['g/w.py']+b'\ndef later():\n    from student_pilot import absent_gpu_submodule\n'})
        self.assertFalse(result['passed'])
        self.assertTrue(any(r.get('name')=='student_pilot.absent_gpu_submodule' for r in result['unresolved']))

    def test_unreviewed_dynamic_loader_fails(self):
        result=A.audit(self.raw,{'g/w.py':self.files['g/w.py']+b'\ndef later(name):\n    import importlib\n    importlib.import_module(name)\n'})
        self.assertFalse(result['passed'])
        self.assertTrue(any(r.get('kind')=='dynamic' for r in result['unresolved']))

if __name__=='__main__':unittest.main(verbosity=2)
