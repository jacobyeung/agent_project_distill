from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_reads228/work/round1/kit/tests/test_kit.py')
s=p.read_text().replace("'A4", "'A10b").replace('A4/','A10b/').replace('step\'],200','step\'],400')
s=s.replace("self.assertEqual(export['step'],200)","self.assertEqual(export['step'],400)")
s=s.replace("self.assertEqual(budget['estimated_peak_bytes'],120716601141)","self.assertEqual(budget['estimated_peak_bytes'],124166664744)")
s=s.replace("self.assertTrue(str(mapped).startswith('/scratch/jjyeung/a4228/archives/'))", "self.assertTrue(str(mapped).startswith('/scratch/jjyeung/orch_n30/reads228/'))")
s=s.replace("WORK=Path('/scratch/jjyeung/orch_n30/so_reads228/work/tests')", "WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/tests_round1'))")
s=s.replace('def copy_reference():','def copy_reference(*, local_provenance=True):')
s=s.replace('    return dest\n\ndef edit_rows', '''    if local_provenance:
        write(dest/'metadata/LOCAL_RUN.json',dict(backend='trinity-local',host='trinity-2-28',mode='OFF',synthetic_cpu_fixture=True))
        write(dest/'metadata/CARDS.json',dict(snapshot=dict(name='NVIDIA RTX 6000 Ada Generation')))
        identity=read(dest/'metadata/RETURN_ID.json');identity['job']='314159265'
        identity['token']=identity['token'][:-8]+format(314159265,'08x');write(dest/'metadata/RETURN_ID.json',identity)
        for path in (dest/'metadata/reads').glob('*/metadata/journals/*/*/environment.json'):
            value=read(path);value['host']='trinity-2-28';write(path,value)
    return dest

def edit_rows''')
s=s.replace("        self.assertEqual(result['verdict'],'SAME_INSTRUMENT')\n        self.assertEqual(result['identical']['answer'],50);self.assertEqual(result['identical']['call_placement'],50)", "        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY')\n        self.assertFalse(result['eligible'])\n        self.assertIn('trinity: missing LOCAL_RUN.json',result['ineligibility_reasons'])",1)
s=s.replace("env=dict(versions=dict(torch='2.11.0+cu129',torchvision='example',transformers='5.12.1',scipy='example'),\n                 python='/scratch/jjyeung/envs/a4228/bin/python',cuda='12.9',prefix='/scratch/jjyeung/envs/a4228',\n                 base_prefix='/scratch/jjyeung/envs/a4228',module_paths={})", "env=dict(versions=read(HERE/'STAGE_PLAN.json')['environment']['versions'],\n                 python='/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e/bin/python',cuda='13.0',\n                 prefix='/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e',\n                 base_prefix='/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu',module_paths={},\n                 python_version=[3,12,13],audit_roots=['/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e/lib/python3.12/site-packages'])")
s=s.replace("stage228.versions('python',dict(versions=env['versions']),{}),env", "stage228.versions('python',dict(versions=env['versions']),{'TMPDIR':str(directory())})['versions'],env['versions']")
s=s.replace("stage228.versions('python',dict(versions={}),{})", "stage228.versions('python',dict(versions={}),{'TMPDIR':str(directory())})")
s=s.replace("stage228.versions('python',dict(versions=env['versions']),{})", "stage228.versions('python',dict(versions=env['versions']),{'TMPDIR':str(directory())})")
s=s.replace("        accepted=HERE/'test_returns'/out.name", """        operator=out/'operator';operator.mkdir()
        for name in ('tower_sequence.py','unpack_return.py','fetch_return.py'):
            shutil.copyfile(HERE/'A10b'/name,operator/name)
        (operator/'src').symlink_to(HERE/'A10b/src',target_is_directory=True)
        (operator/'package').symlink_to(HERE/'A10b/package',target_is_directory=True)
        accepted=out/'accepted'""")
s=s.replace("'--operator',str(HERE/'A10b'),", "'--operator',str(operator),")
s=s.replace("str(directory()/'out')],\n                              text=True,capture_output=True)", "str(directory()/'out')],\n                              env=dict(os.environ,READ228_CONTROL_PYTHON=sys.executable),text=True,capture_output=True)")
s=s.replace("        self.assertEqual(commands[0][:5],['nice','-n','10','bash',str(runner228.VNICE)])", "        self.assertEqual(commands[0][:5],['nice','-n','10','bash',str(runner228.VNICE)])\n        self.assertTrue((out/'ret/metadata/reads/0/metadata/IDENTITY.json').is_file())\n        self.assertTrue((out/'ret/metadata/reads/0/metadata/projection.json').is_file())")
# CPU fixtures authenticate the supplied small policy scripts; they never run vnice.
s=s.replace("import return228\n", "import return228\nimport common228\ncommon228.VNICE=HERE/'evidence/q/vnice.sh'\ncommon228.TERMINATOR=HERE/'evidence/q/terminator.sh'\n")
p.write_text(s)
print('Adapted the baseline 39 tests to A10b and work-only fixtures.')
