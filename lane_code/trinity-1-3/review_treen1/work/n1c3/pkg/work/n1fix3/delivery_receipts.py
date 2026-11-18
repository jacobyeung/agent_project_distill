from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()
source=inventory(T);seal=json.loads((L/'out/TREE_SEAL.json').read_text())
assert digest(source)==seal['tree_sha256']
packet=B/'proofs/packet';result=json.loads((packet/'results.json').read_text())
assert all(r['outcome']=='passed' for r in result.values())
python=json.loads((packet/'coverage/source_hashes.json').read_text())
assert all(source[name]==h for name,h in python.items())
inputs={}
for row in json.loads((B/'PACKET_INPUTS.json').read_text()):
    p=L/row['source'];assert sha(p)==row['sha256'];inputs[row['source']]=row['sha256']
receipt=dict(complete=True,source=source,fixtures=inventory(L/'fixtures'),
    contract_tests=inventory(L/'work/contracts_r6/packet_root/work/tests_r6'),inputs=inputs,
    runner_sha256=sha(B/'packet_final.py'),results_sha256=sha(packet/'results.json'),
    result_source='work/n1fix3/proofs/packet/results.json',command='packet_final.py integrated packet contract')
(B/'PACKET_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
delivery=json.loads((B/'DELIVERY.json').read_text());archive=L/delivery['path']
frozen=json.loads((B/'proofs/package/ARCHIVE.json').read_text())
assert sha(archive)==delivery['sha256']==frozen['sha256']
assert digest(source)==frozen['source_sha256']
assert inventory(B/'proofs/package/frozen/work/tree_r1')==source
groups=[]
for name in ('generator','legacy','r2'):
    p=B/'proofs/suite_tree'/name/'GROUP_RECEIPT.json';value=json.loads(p.read_text())
    assert value['complete'] and value['inputs']['source']==source
    groups.append(dict(group=name,receipt_sha256=sha(p)))
(B/'FINAL_SOURCE_RECEIPT.json').write_text(json.dumps(dict(complete=True,seal=digest(source),
    package_sha256=delivery['sha256'],packet_receipt_sha256=sha(B/'PACKET_RECEIPT.json'),groups=groups),indent=2))
print(json.dumps(dict(seal=digest(source),packet_tests=len(result),groups_verified=len(groups))))
