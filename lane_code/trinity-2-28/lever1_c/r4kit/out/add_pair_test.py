from pathlib import Path
p=Path('src/runtime.py');s=p.read_text()
pos=s.index('\ndef run(')
s=s[:pos]+'''
class PairWriter:
    def __init__(self, stream, rows, progress, started):
        self.stream, self.rows, self.progress, self.started = stream, rows, progress, started
        self.pending = {}

    def emit(self, i, result):
        row = self.rows[i]
        result.update(i=row['i'], r=row['r'], a=row['a'], s=time.monotonic()-self.started)
        self.pending[i] = result
        pair = i-i%2
        if pair in self.pending and pair+1 in self.pending:
            raw = b''.join(C.pack(json.dumps(self.pending[j], sort_keys=True, allow_nan=False)) for j in (pair,pair+1))
            assert len(raw) <= 262144 and self.stream.tell()+len(raw) < 49000000
            self.stream.write(raw); self.stream.flush(); os.fsync(self.stream.fileno())
            self.progress[0] += 2
            del self.pending[pair]; del self.pending[pair+1]

''' +s[pos:]
s=s.replace('    records = 0\n', '    progress = [0]\n')
a=s.index('                pending = {}');b=s.index('                batches = None',a)
s=s[:a]+'''                writer = PairWriter(stream, rows, progress, t0)
                batched.generate(model, processor, batches, probe, writer.emit, deadline)
''' +s[b:]
s=s.replace("        write(out/'1.json', dict(passed=status=='complete' and records==580", "        records = progress[0]\n        write(out/'1.json', dict(passed=status=='complete' and records==580")
p.write_text(s)
p=Path('tests/test_fixes.py');s=p.read_text();pos=s.index('\nORIGINAL_MATERIALIZE=')
s=s[:pos]+'''
    def test_07_partial_pair_writer_and_fetch(self):
        runtime=mod('partial_runtime',ROOT/'src/runtime.py');runtime.C=C
        p,cfg,_=package();records=p/'z/a';records.mkdir(parents=True)
        rows=[dict(i=str(i//2),r='a',a=i%2) for i in range(8)]
        progress=[0]
        with (records/'0.jsonl').open('wb') as stream:
            writer=runtime.PairWriter(stream,rows,progress,time.monotonic())
            item=dict(text='<ground',tokens=[27,1884],n=2,g=True,o=[],finish='call')
            writer.emit(0,dict(item));self.assertEqual(stream.tell(),0)
            writer.emit(1,dict(item));self.assertEqual(progress,[2])
            writer.emit(3,dict(item));self.assertEqual(progress,[2])
        ctl.finalize(p,records,cfg,'g','123',time.time(),1,ctl.Deadline())
        ctl.fetch(p,p/'f');returned=members((p/'f/0.tgz').read_bytes())
        result=[C.loads(line) for line in returned['0.jsonl'].splitlines()]
        self.assertEqual([(r['i'],r['a']) for r in result],[('0',0),('0',1)])
        self.assertEqual(C.loads(returned['1.json'])['records'],2)
        self.assertFalse(ctl.read(p/'f/1.json')['passed'])
        scan(records)
        EVIDENCE['partial_pairs']=dict(completed_pairs=1,unfinished_arm_omitted=True,real_fetch=True)

''' +s[pos:]
p.write_text(s)
