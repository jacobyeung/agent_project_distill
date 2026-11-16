import os, sqlite3, sys, tempfile, json, random, tarfile, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlro

def make(path, n, big=False):
    c = sqlite3.connect(path); c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,target TEXT NOT NULL)')
    rnd = random.Random(3)
    for i in range(n):
        size = rnd.choice([10, 500, 5000, 70000]) if big else 50
        c.execute('insert into rows values(?,?,?)', (i, json.dumps({'k': i, 'pad': 'é' * size}), '{}'))
    c.commit(); c.close()

def expect(path):
    c = sqlite3.connect(path); return [(r[0], r[1], r[2]) for r in c.execute('select i,row,target from rows order by i')]

def test_plain_and_overflow():
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/scratch/jjyeung/orch_n30/b06_a2dense/dense/tmp'))
    p = os.path.join(d, 'a.sqlite'); make(p, 3000, big=True)
    got = [(rid, v[1], v[2]) for rid, v in sqlro.Store(sqlro.SplitFile([p])).rows('rows')]
    assert got == expect(p)

def test_split_parts_and_tar():
    d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/scratch/jjyeung/orch_n30/b06_a2dense/dense/tmp'))
    p = os.path.join(d, 'b.sqlite'); make(p, 2000, big=True)
    data = open(p, 'rb').read(); cut = [0, 777777, 1500001, len(data)]
    parts = []
    for k in range(3):
        q = os.path.join(d, 'b.p%02d' % k); open(q, 'wb').write(data[cut[k]:cut[k + 1]]); parts.append(q)
    got = [(rid, v[1], v[2]) for rid, v in sqlro.Store(sqlro.SplitFile(parts)).rows('rows')]
    assert got == expect(p)
    t = os.path.join(d, 'x.tar')
    with tarfile.open(t, 'w') as tf:
        tf.add(p, arcname='ap/r/rows.sqlite')
    off, size = sqlro.tar_member(t, 'ap/r/rows.sqlite')
    got = [(rid, v[1], v[2]) for rid, v in sqlro.Store(sqlro.SplitFile([t], off, size)).rows('rows')]
    assert got == expect(p)
