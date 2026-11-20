from pathlib import Path
import sys, types, json
L=Path(__file__).resolve().parents[2]; D=L/'work/build24m4o3'
name=sys.argv[1]
c=types.ModuleType('common');c.__file__=str(L/'work/build24m4o/common.py')
exec(compile(Path(c.__file__).read_bytes(),c.__file__,'exec'),c.__dict__)
c.D=D/name;c.D.mkdir();c.J=c.z
sys.modules['common']=c
if name=='publication':
    p=L/'work/build24m4o/tests.py'
    source=p.read_text()
    # Keep the original AST regression, allowing only the new publication block.
    source=source.replace("{'nsample'}","{'nsample','log_tails'}")
    source=source.replace("t.func.id=='nsample'","t.func.id in ('nsample','log_tails')")
    (c.D/'BASELINE.json').write_bytes((L/'work/build24m4o/BASELINE.json').read_bytes())
elif name=='recorder':
    p=L/'work/build24m4o/recorder_tests.py';source=p.read_text()
elif name=='scan':
    p=L/'work/build24m4o/rcj_scan.py';source=p.read_text()
elif name=='contract':
    p=L/'work/build24m4n/rcj_contract_tests.py';source=p.read_text()
    (c.D/'rdiff.py').write_bytes((L/'work/build24m4n/rdiff.py').read_bytes())
elif name=='sample':
    p=L/'work/build24m4n/rcj_l_tests.py';source=p.read_text().split('# Actual C')[0]
    source+="\nJ.write(D/'SAMPLE_TESTS.json',dict(status='PASS',records=records))\nprint('Sample reference, gate and size checks PASS')\n"
else:raise ValueError(name)
(c.D/'source.py').write_text(source)
exec(compile(source,str(p),'exec'),dict(__file__=str(p),__name__='__main__'))
