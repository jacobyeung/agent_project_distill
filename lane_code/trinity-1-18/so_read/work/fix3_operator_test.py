from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py');s=p.read_text()
s=s.replace('    observed=[]','    observed=[];overlays=[]',1)
s=s.replace("            with patch.object(sys,'argv',argv[-2:]):runpy.run_path(argv[-2],run_name='__main__')", """            with patch.object(sys,'argv',argv[-2:]):runpy.run_path(argv[-2],run_name='__main__')
            from e2e_reader import read_cache,parity,stage1
            for module,name in ((read_cache,'a0.py'),(parity,'a1.py'),(stage1,'a3.py')):
                assert Path(module.__file__).read_bytes()==(p/'u0'/name).read_bytes()
                overlays.append(name)""")
s=s.replace("        from e2e_reader import read_cache,parity,stage1\n        for module,name in ((read_cache,'a0.py'),(parity,'a1.py'),(stage1,'a3.py')):\n            assert Path(module.__file__).read_bytes()==(p/'u0'/name).read_bytes()", "        assert overlays==['a0.py','a1.py','a3.py']")
p.write_text(s)
