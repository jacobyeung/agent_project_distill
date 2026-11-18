from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';old=L.parent/'w10/work/build10/proofs'
comparisons=[]
prior_n=L.parent/'wn2/work/n1fix2/proofs'
for proof,fields in [('text',['families']),('forward',['status','loss','supervised_tokens','nonzero_finite_gradient_tensors'])]:
    left=prior_n/proof/'RESULT.json';right=B/'proofs/n1'/proof/'RESULT.json'
    a=json.loads(left.read_text());b=json.loads(right.read_text())
    if proof=='text':
        av={k:v['counts'] for k,v in a['families'].items()};bv={k:v['counts'] for k,v in b['families'].items()}
    else:av={k:a[k] for k in fields};bv={k:b[k] for k in fields}
    comparisons.append(dict(proof='n1_'+proof,source=str(left),current=str(right.relative_to(L)),equal=av==bv,before=av,after=bv))
for proof,file,fields in [('parity','NUMERIC_PARITY.json',['status','counts']),('parity_build7','RESULT.json',['status','counts'])]:
    a=json.loads((old/proof/file).read_text());b=json.loads((B/'proofs'/proof/file).read_text())
    comparisons.append(dict(proof=proof,source=str(old/proof/file),current=str((B/'proofs'/proof/file).relative_to(L)),fields=fields,equal=all(a[k]==b[k] for k in fields)))
table={}
for reader in ('gf1','c8r','b04'):
    left=old/'eat1'/reader/'run/EAT1_REPORT.json';right=B/'proofs/eat1'/reader/'run/EAT1_REPORT.json'
    a=json.loads(left.read_text());b=json.loads(right.read_text())
    av={k:v['status'] for k,v in a['clauses'].items()};bv={k:v['status'] for k,v in b['clauses'].items()}
    table[reader]=bv
    comparisons.append(dict(proof='eat1/'+reader,source=str(left),current=str(right.relative_to(L)),equal=av==bv,before=av,after=bv))
mut=B/'proofs/n1/mutations/RESULT.json';rows=json.loads(mut.read_text())['results']
comparisons.append(dict(proof='n1_mutations',current=str(mut.relative_to(L)),equal=all(r['clean_pass'] and r['caught'] and not r['errors'] for r in rows)))
record=dict(comparisons=comparisons,eat1=table,all_equal=all(r['equal'] for r in comparisons))
(B/'PROOF_EQUALITY.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));assert record['all_equal']
