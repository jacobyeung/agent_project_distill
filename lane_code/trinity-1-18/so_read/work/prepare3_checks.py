from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0'
p=E/'tests/test_operator_round3.py';s=p.read_text();needle="        self.assertEqual(operator.memory_bound(read_cache_bytes=12*1024**3),baseline)"
s=s.replace(needle,needle+'''
        sys.path[:0]=[str(SRC/'u0'),str(SRC),str(SRC/'b'),str(INPUT/'tree')]
        from a8 import activate
        activate(enabled=True)
        root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
        settings=root/'settings.json'
        settings.write_text(json.dumps(dict(perception_memo_modules=['g3t'],read_sam_cache='on',read_cache_bytes=12*1024**3)))
        cfg=dict(settings=str(settings),output=str(root),read_extensions=True)
        self.assertEqual(operator.memory_probe(cfg),on)
        cfg['read_extensions']=False
        self.assertEqual(operator.memory_probe(cfg),baseline)
''');p.write_text(s)
p=L/'work/run_checks.py';s=p.read_text()
s=s.replace("('round2','work/src/u0/tests/test_round2.py'),", "('round2','work/src/u0/tests/test_round2.py'),\n                  ('round3','work/src/u0/tests/test_round3.py'),\n                  ('operator3','work/src/u0/tests/test_operator_round3.py'),\n                  ('lock3','work/src/u0/tests/test_lock_round3.py'),")
needle="assert (L/'work/src/u0/a9.py').read_bytes()"
pos=s.index(needle)
s=s[:pos]+'''
for name,script,variable,summary,args in (
    ('round3_before','test_round3.py','READ_ROUND3_BEFORE','FAILED (failures=14)',[]),
    ('operator3_before','test_operator_round3.py','READ_ROUND3_BEFORE','FAILED (failures=2)',[]),
    ('lock3_before','test_lock_round3.py','READ_LOCK_BEFORE','FAILED (failures=2)',[]),
    ('f16_behavior_before','test_round3.py','READ_F16_BEFORE','FAILED (failures=1)',
     ['Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'])):
    command=[sys.executable,'-I','-s','-B',str(L/'work/src/u0/tests'/script),*args]
    result=subprocess.run(command,env=dict(env,**{variable:'1'}),cwd=L,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/(name+'.txt')).write_text(result.stdout)
    assert result.returncode==1 and summary in result.stdout,result.stdout
    print('PASS: '+name+' reproduces '+summary+'.')
''' +s[pos:]
s=s.replace("print('PASS: Python syntax, shell syntax, and default-off execution guards.')","print('PASS: Python syntax, shell syntax, and default-off execution guards.')")
p.write_text(s)
