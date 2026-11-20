from common import *
s=(D/'rcj_l_tests.py').read_text().split('# Actual C')[0]
s=s.replace("F=D/'rcj_l'","F=D/'sample_final'")
exec(compile(s,str(D/'rcj_l_tests.py'),'exec'))
J.write(D/'SAMPLE_FINAL_TESTS.json',dict(status='PASS',records=records,script_sha256=J.sha(L/'out/rcj/ps.py'),wrapper_sha256=J.sha(L/'out/rcj/x.py')))
print('Final sample gate, reference equality and size refusal PASS')
