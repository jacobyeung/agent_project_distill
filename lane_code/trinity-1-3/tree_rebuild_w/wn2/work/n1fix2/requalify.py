"""Apply the exact reviewer normalization cases and qualify the resulting snapshot."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
p=T/'student_pilot/row_text_audit.py';s=p.read_text()
s=s.replace("    stripped = ''.join(c for c in text if unicodedata.category(c) != 'Cf'", "    text = unicodedata.normalize('NFKD', text).translate({0x435:'e',0x415:'E'})\n    stripped = ''.join(c for c in text if unicodedata.category(c) not in ('Cf','Mn','Me')")
s=s.replace("    def normalize(value):\n", "    def normalize(value):\n        value = unicodedata.normalize('NFKD',value).replace('е','e').replace('Е','E')\n        value = ''.join(c for c in value if not unicodedata.combining(c))\n")
p.write_text(s)
(L/'out/MIX_R1.json').write_bytes((B/'inputs/mix.json').read_bytes())
if (B/'kits').exists():
    retained=B/'proofs/kits_before_normalization'
    assert not retained.exists()
    (B/'kits').rename(retained)
(B/'REQUALIFICATION.json').write_text(json.dumps(dict(pending=False,reason='Exact reviewer variants included in independent normalizers.')))
with (B/'DECISIONS.md').open('a') as f:f.write('\nThe complete reviewer variant set also contains fullwidth text, a Cyrillic e and an accented e. Default: apply compatibility decomposition, strip combining marks and normalize the specified Cyrillic e in each independent admission check. This affects input admission only.\n')
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
py=[sys.executable,'-I','-s','-B']
def run(name,args,allow=False):
    (B/'STATUS.md').write_text('Build n1fix2: '+name+' is running on the final normalized source. GO=false. Evidence: proofs/ and '+name+'.log.\n')
    key=dict(source=inventory(T),scripts={str(Path(a).relative_to(L)):hashlib.sha256(Path(a).read_bytes()).hexdigest() for a in args if Path(a).is_file() and Path(a).is_relative_to(L)})
    receipt=B/(name+'_RECEIPT.json')
    if receipt.exists() and json.loads(receipt.read_text()).get('inputs')==key and json.loads(receipt.read_text()).get('complete'):
        print('Resume '+name,flush=True);return
    with (B/(name+'.log')).open('w') as log:code=subprocess.run(args,cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    if code<0:raise SystemExit('Process killed; stop without retry: '+name)
    receipt.write_text(json.dumps(dict(inputs=key,complete=code==0,returncode=code),indent=2))
    print(name+': '+str(code),flush=True)
    if code and not allow:raise SystemExit(name+' failed')
for name,args in [
 ('review_variants',py+[str(B/'proof_review_variants.py')]),
 ('targeted',py+[str(B/'test_runner.py'),str(B/'proofs/targeted'),'tests.test_r2_n1fix','tests.test_r2_n1fix2','tests.test_r2_build_n1']),
 ('text',py+[str(B/'proof_text.py')]),
 ('packet',['bash',str(B/'PACKET_TEST.sh')]),
 ('seal',py+[str(B/'seal.py')]),
 ('kits',py+[str(B/'stage9.py')]),
 ('delivery',py+[str(B/'make_delivery.py')])]:run(name,args)
delivery=json.loads((B/'DELIVERY.json').read_text())
run('package',['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])],allow=True)
(B/'STATUS.md').write_text('Final source phases finished. Coverage and suite comparison remain pending. GO=false.\n')
