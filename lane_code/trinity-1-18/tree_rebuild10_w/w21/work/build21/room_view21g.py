"""Run the exact room-count entry on a tiny, explicitly synthetic store."""
from pathlib import Path
import datetime,json,sqlite3,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
view=J.load(D/'VIEW.json');v=view['variables'];node=Path(v['Q_ROOT']);ns=v['Q_NS']
root=node/'count';root.mkdir(exist_ok=True)
database=root/'rows.sqlite'
assert not database.exists()
rows=[dict(qid='q0',dataset='d1',scene='scene9997_00',canonical='scannet/scene9997_00',question_type='q'),
      dict(qid='q1',dataset='d1',scene='scene9997_00',canonical='scannet/scene9997_00',question_type='q')]
with sqlite3.connect(database) as db:
    db.execute('CREATE TABLE rows (i INTEGER, row TEXT)')
    db.executemany('INSERT INTO rows VALUES (?,?)',[(i,json.dumps(row)) for i,row in enumerate(rows)])
receipt=J.write(root/'receipt.json',dict(database=dict(path=str(database),sha256=J.sha(database))))
cfg=J.load(K/'k/n.json');cfg['streams']={'q':receipt};J.write(root/'config.json',cfg)
request=J.load(node/'native.json');J.write(root/'request.json',dict(_paths=request['_paths']))
args=J.load(D/'proofs/view/after.json')+[sys.executable,'-s','-B',str(K/'b/d.py'),ns+'/p/s',
    ns+'/count/request.json',ns+'/count/config.json',ns+'/count/rooms.json']
p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
value=J.load(root/'rooms.json') if (root/'rooms.json').exists() else None
record=dict(command=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,result=value,
    stand_ins='Two synthetic rows in a new SQLite store; real pinned room authority and withheld list; exact b/d.py entry and room_report function.',
    production_count_verified=False)
J.write(D/'ROOM_VIEW.json',record)
assert p.returncode==0,(p.stdout,p.stderr)
assert sum(x['rows'] for x in value['cells'].values())==2
assert value['report_only'] is True and value['admission_changed'] is False
print(json.dumps(dict(status='PASS',cells=value['cells'])))
