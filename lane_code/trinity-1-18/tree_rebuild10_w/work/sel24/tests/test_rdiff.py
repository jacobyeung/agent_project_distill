import ast
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import resource

resource.setrlimit(resource.RLIMIT_AS, (8 << 30, 8 << 30))
S = Path(__file__).resolve().parents[1]
T = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/work/tree_r1')
source = T/'student_pilot/s1_routing.py'
create = []
for node in ast.walk(ast.parse(source.read_text())):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'execute' and node.args:
        a = node.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith('CREATE '):
            create.append(a.value)
assert any('CREATE VIEW rows ' in x for x in create)


def row(qid, source='U_Faithful', **extra):
    return dict(qid=qid, dataset='d0', scene='s0', s1_source=dict(name=source), **extra)


def db(path, entries, flat=False):
    with sqlite3.connect(path) as con:
        if flat:
            module=ast.parse((T/'student_pilot/carrier_c1_routing.py').read_text())
            sql=[n.args[0].value for n in ast.walk(module) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str) and n.args[0].value.startswith('CREATE TABLE rows ')][0]
            con.execute(sql)
        else:
            for sql in create: con.execute(sql)
        for i, raw, target in entries:
            r=json.loads(raw)
            if flat:
                con.execute('INSERT INTO rows VALUES (?,?,?)',(i,raw,target))
            else:
                con.execute('INSERT INTO candidates VALUES (?,?,?,?,?,?)',(i,r['qid'],'object_abs_distance','pool_program',r['s1_source']['name'],raw))
                con.execute('INSERT INTO membership VALUES (?,?)',(i,i))


def ent(i, r, target='{}'):
    return i,json.dumps(r),target

results=[]
def case(name,p,n,lists,expect,flat=False,expected_pin='none'):
    root=S/'tests'/name;root.mkdir()
    db(root/'0.sqlite',p,flat);db(root/'1.sqlite',n,flat)
    rules=[]
    for j,(text,defects) in enumerate(lists):
        f=root/f'{j}.json';f.write_text(text)
        rule=dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        if defects is not None:rule['defects']=defects
        rules.append(rule)
    (root/'2.json').write_text(json.dumps(rules))
    argv=[sys.executable,'-I','-s','-B',str(S/'orchard/rdiff.py'),str(root/'1.sqlite'),str(root/'0.sqlite'),'--tree',str(T),'--out',str(root/'o'),'--removal-manifest',str(root/'2.json'),'--expected-p-sha256',expected_pin]
    run=subprocess.run(argv,text=True,capture_output=True)
    (root/'run.json').write_text(json.dumps(dict(argv=argv,returncode=run.returncode,stdout=run.stdout,stderr=run.stderr),indent=2))
    assert run.returncode==expect.pop('exit'),(name,run.stdout,run.stderr)
    if run.returncode!=2:
        import gzip
        summary=json.loads((root/'o/rdiff_summary.json').read_text())
        data=json.loads(gzip.decompress((root/'o/rdiff.json.gz').read_bytes()))
        assert len(data['N'])==summary['N_rows']
        assert len(data['P_absent'])==summary['P_rows_absent_from_N']
        for k,v in expect.items(): assert summary[k]==v,(name,k,summary[k],v)
        assert summary['script_sha256']==hashlib.sha256((S/'orchard/rdiff.py').read_bytes()).hexdigest()
    results.append(dict(name=name,status='PASS',returncode=run.returncode))

r0,r1=ent(0,row('a')),ent(1,row('b',label_row_keys=['alias']))
case('00',[r0,r1],[r0,r1],[],dict(exit=0,matched_identical=2,mismatched=0))
case('01',[r0,r1],[r0],[(json.dumps(dict(row_key='alias'))+'\n',None)],dict(exit=0,matched_identical=1,absent_and_listed=1,U_Faithful=dict(P=2,N=1,listed=1,absent_listed=1,N_listed=0)))
case('02',[r0,r1],[r0],[],dict(exit=1,absent_and_unlisted=1))
case('03',[r0],[ent(0,row('a',x=1))],[],dict(exit=1,mismatched=1))
case('04',[r0],[ent(2,row('a'))],[],dict(exit=1,mismatched=1))
case('05',[r0],[ent(0,row('a'),'{"x":1}')],[],dict(exit=1,mismatched=1),flat=True)
case('06',[r0],[(0,r0[1]+' ',r0[2])],[],dict(exit=1,mismatched=1))
case('07',[r0],[r0,ent(1,row('c'))],[],dict(exit=1,N_rows_without_P=1,mismatched=1))
case('08',[r0,r1],[r0],[(json.dumps(dict(row_key='alias',defect='extent'))+'\n',['identity'])],dict(exit=1,absent_and_unlisted=1))
case('09',[r0,r1],[r0],[(json.dumps(dict(row_key='alias',defect='identity|extent'))+'\n',['identity'])],dict(exit=0,absent_and_listed=1))
naming=(S/'evidence/d1454a4461e96fda9e0db27eb75fe0080a555d77a4d05f8e036d49530626db29').read_text()
qid=json.loads(naming)['rows'][0]['qid']
case('10',[r0,ent(1,row(qid))],[r0],[(naming,None)],dict(exit=0,absent_and_listed=1))
case('11',[r0],[r0],[],dict(exit=2),expected_pin='0'*64)
case('12',[r0,ent(1,row('a'))],[r0],[],dict(exit=2))
case('13',[r0],[r0],[(json.dumps(dict(row_key='a'))+'\n',None)],dict(exit=1,N_rows_listed=1))
(S/'tests/RESULTS.json').write_text(json.dumps(dict(status='PASS',schema_source=str(source),schema_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),create_sql=create,tests=results),indent=2)+'\n')
print(json.dumps(dict(status='PASS',tests=len(results))))
