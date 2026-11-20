from pathlib import Path
import base64,hashlib,json,shutil,os,tarfile,sys
J=Path.cwd();D=J/'work/build24m4z4';K=J/'out/kit_n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v
def encoded(p,v):
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 p.write_text(json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True)+'\n')
files=['b/o.py','b/pc.py','b/pc.sh','k/y.json','SHA256SUMS.txt','BUILD.json']
before={}
for root in ('out/kit_n','out/kit_n_go','work/build24/kits/n'):
 before[root]=load(J/root/'BUILD.json')['kit_sha256']
 for name in files:
  p=J/'attic/build24m4z4'/root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(J/root/name,p)
for p in (J/'out/e2').iterdir():shutil.copy2(p,J/'attic/build24m4z4'/p.name)
(D/'BEFORE.json').write_text(json.dumps(before,indent=2)+'\n')
o='''import json,sys,tarfile,os,shutil,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write,name_guard
from pc import CAP,LOG_CAP
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID']
safe=name_guard(k)
local=r/'o';local.mkdir(parents=True,exist_ok=True)
# Freeze one bounded archive per allocation; retries must use identical bytes.
if not (local/'o.tar').exists():
 write(local/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]),GO=False,submitted_by_build=False))
 logs=[r/n for n in ('q.log','rooms.log','h.log','t.log') if (r/n).is_file() and not (r/n).is_symlink()]
 metadata=[local/'RESULT.json']+[r/n for n in ('rooms.json','p/q/RESULT.json','p/q/host.json','p/q/f.json') if (r/n).is_file() and not (r/n).is_symlink()]
 pending=[];remaining=LOG_CAP
 for i,p in enumerate(logs):
  allowance=remaining//(len(logs)-i)
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-allowance));raw=f.read(allowance)
  pending.append((safe(str(p.relative_to(r))),raw));remaining-=len(raw)
 remaining=CAP-LOG_CAP-1_000_000
 for p in metadata:
  if p.stat().st_size>remaining:continue
  with p.open('rb') as f:raw=f.read(remaining+1)
  if len(raw)>remaining:continue
  pending.append(('RESULT.json' if p==local/'RESULT.json' else safe(str(p.relative_to(r))),raw));remaining-=len(raw)
 partial=local/'o.tar.part'
 with tarfile.open(partial,'w:gz',format=tarfile.USTAR_FORMAT) as t:
  for name,raw in pending:
   m=tarfile.TarInfo(name);m.size=len(raw);m.mode=0o600;t.addfile(m,io.BytesIO(raw))
 if partial.stat().st_size>CAP:raise ValueError('E103')
 os.replace(partial,local/'o.tar')
if '--local' not in sys.argv:
 try:
  out.mkdir(parents=True,exist_ok=True)
  for name in ('o.tar','RESULT.json'):
   shutil.copyfile(local/name,out/(name+'.part'))
   os.replace(out/(name+'.part'),out/name)
 except OSError as error:
  with (local/'retry.log').open('a') as stream:stream.write('E'+str(error.errno)+'\\n')
'''
(K/'b/o.py').write_text(o)
p=K/'b/pc.py';s=p.read_text()
s=s.replace('        self.final_pass = False','        self.final_pass = False\n        self.exit_status = None')
s=s.replace('def send(self, directory, marker, labels):','def send(self, directory, marker, labels, archive=None):')
s=s.replace('        archive = self.archive(directory, marker)','        archive = self.archive(directory, marker) if archive is None else Path(archive)')
start=s.index("        local = self.root/'o'",s.index('    def _small'))
end=s.index('    def archive(',start)
s=s[:start]+'''        self.copy_exit()
        return total + len(raw)

    def copy_exit(self):
        local = self.root/'o'
        for name in ('o.tar', 'RESULT.json'):
            source = local/name
            if source.is_file():
                destination = self.target/'o'/self.job/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                partial = destination.with_name(name+'.part')
                shutil.copyfile(source, partial)
                os.replace(partial, destination)

    def exit_archive(self):
        archive = self.root/'o/o.tar'
        if not archive.is_file() and self.exit_status is not None:
            # The final pass reaches this only after the stop, exports and logs.
            with open('/dev/null', 'wb') as quiet:
                subprocess.run([sys.executable, '-I', '-s', '-B', str(self.kit/'b/o.py'),
                    str(self.root), str(self.exit_status), '0', '--local'],
                    env={**os.environ, 'SLURM_JOB_ID':self.job},
                    stdout=quiet, stderr=quiet, check=True)
        if archive.is_file():
            if archive.stat().st_size > CAP:
                raise ValueError('E103')
            # The marker is the immutable archive itself; send verifies every part.
            self.send(archive.parent, archive, ['o'], archive=archive)
            self.attempt('o_copy', self.copy_exit)

''' +s[end:]
start=s.index('            if small:\n',s.index('    def pass_once'))
end=s.index('\n\ndef main',start)
s=s[:start]+'''            if final:
                phases = [('stop', [self.stop_checkpoint]),
                          ('exports', [self.exports, self.checkpoints]),
                          ('logs', [self.small] if small else []),
                          ('o', [self.exit_archive])]
                for label, actions in phases:
                    with (self.spool/'final_order.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(phase=label, time=time.time()))+'\\n')
                    for action in actions:
                        self.attempt(action.__name__, action)
            else:
                if small:
                    self.attempt('small', self.small)
                for action in (self.checkpoints, self.exports, self.exit_archive):
                    self.attempt(action.__name__, action)
''' +s[end:]
s=s.replace("    p.add_argument('--prepare', action='store_true')","    p.add_argument('--prepare', action='store_true')\n    p.add_argument('--status', type=int, default=0)")
s=s.replace("    if args.prepare:\n", "    c.exit_status = args.status if args.final else None\n    if args.prepare:\n")
s=s.replace("        if not args.loop:\n            return", "        if not args.loop:\n            if args.final and not (c.state/'gcs_o.done').is_file():\n                time.sleep(2)\n                continue\n            return")
p.write_text(s)
p=K/'b/pc.sh';s=p.read_text().replace('"$SLURM_JOB_ID" --final || true','"$SLURM_JOB_ID" --final --status "$status" || true')
s=s.replace('    python3 -B -I -s "$ROOT/b/o.py" "$N" "$status" 0 || true\n','');p.write_text(s)
p=K/'k/y.json';v=load(p);v['objects']['o']='q9/22c714e1/469ddece_o.tar';encoded(p,v)
for root in ('out/kit_n_go','work/build24/kits/n'):
 for name in files[:4]:shutil.copy2(K/name,J/root/name)
for root in ('out/kit_n','out/kit_n_go','work/build24/kits/n'):
 k=J/root;names=[s.split('  ',1)[1] for s in (k/'SHA256SUMS.txt').read_text().splitlines()]
 (k/'SHA256SUMS.txt').write_text(''.join(sha(k/n)+'  '+n+'\n' for n in names))
 v=load(k/'BUILD.json');v['kit_sha256']=sha(k/'SHA256SUMS.txt');encoded(k/'BUILD.json',v)
for name in files:os.chmod(J/'work/build24/kits/n'/name,(K/name).stat().st_mode&511)
print('CHANGED',json.dumps({r:load(J/r/'BUILD.json')['kit_sha256'] for r in before}))
