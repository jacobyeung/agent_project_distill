from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0/tests'
p=E/'test_round4.py';s=p.read_text().replace("        export=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())", "        export=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())\n        for name in MEMBERS:inputs['files'][name].update(export[name])")
s=s.replace('step600_package','bound_package').replace('step600_real','bound_real').replace('CPU step-600 fixture:','CPU bound-export fixture:').replace('A4 step-600 CPU contract','A4 bound-export CPU contract');p.write_text(s)
p=E/'test_round5.py';s=p.read_text().replace("cls.builder=load('builder5',E/'a19.py')", "legacy=any(os.environ.get(k)=='1' for k in ('READ_ROUND6_BEFORE','READ_ROUND7_BEFORE'))\n        cls.builder=load('builder5',(L/'work/round8-before-u0' if legacy else E)/'a19.py')").replace('        if not BEFORE:\n            cls.binding=', '        if not BEFORE and not legacy:\n            cls.binding=');p.write_text(s)
for p in (E/'test_round6.py',L/'work/run_checks.py',L/'work/gate_integration8.py'):
 s=p.read_text().replace('step600_real','bound_real').replace('CPU step-600 fixture:','CPU bound-export fixture:')
 if p.name=='run_checks.py':s=s.replace("'READ_ROUND8_BEFORE','FAILED (failures=27)'","'READ_ROUND8_BEFORE','FAILED (failures=29)'")
 p.write_text(s)
print('Fixed step-400 input pins in synthetic restore fixtures and retained historical fail-before controls.')
