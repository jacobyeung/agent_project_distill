from pathlib import Path
import json,base64,hashlib,difflib,shutil
W=Path(__file__).resolve().parent;J=W.parents[1];K=J/'out/kit_n_go';P=W/'proposed';shutil.copytree(K,P)
s=(K/'b/pc.py').read_text()
s=s.replace("self.claims = self.target/'o'/'gcs_claims'","self.claims = self.root/'live_spool/claims'")
s=s.replace("self.target/'n_s/sess.json'","self.target/'n_s'/('sess_'+self.job+'.json')")
s=s.replace("        self.live.mkdir(parents=True, exist_ok=True)\n",'')
s=s.replace("        self.claims.mkdir(parents=True, exist_ok=True)","        self.claims.mkdir(parents=True, exist_ok=True)\n        self.state = self.spool/'state'\n        self.state.mkdir(exist_ok=True)")
s=s.replace("('CLAIMS', self.claims, self.target/'o/gcs_claims'),\n            ",'')
s=s.replace("    def small(self):",'''    def note(self, label, error):
        with (self.spool/'retry.log').open('a') as stream:
            stream.write(json.dumps(dict(time=int(time.time()), action=label,
                error=type(error).__name__, errno=getattr(error,'errno',None)))+'\\n')

    def attempt(self, label, action):
        try:
            return action()
        except Exception as error:
            self.note(label, error)

    def small(self):''')
s=s.replace("        rows, pending = [], []", "        self.live.mkdir(parents=True, exist_ok=True)\n        rows, pending = [], []")
s=s.replace("        total = 0\n", "        for p in sorted(self.state.glob('*')):\n            if p.is_file() and p.stat().st_size <= metadata_budget:\n                raw = p.read_bytes(); pending.append((p.name, raw)); metadata_budget -= len(raw)\n        total = 0\n")
s=s.replace('# A global project-side lock serializes generations across allocations.','# Allocation-specific object keys and a local lock serialize this allocation.')
s=s.replace("key = self.names['objects'][label]","key = self.names['objects'][label] + '.j' + self.job")
s=s.replace("done = self.live/('gcs_'", "done = self.state/('gcs_'")
s=s.replace("put(self.live/('gcs_'", "put(self.state/('gcs_'")
s=s.replace("put(self.live/'ckstop.json'", "put(self.state/'ckstop.json'")
start=s.index('        self.paths()\n        destination = self.checkpoint',s.index('    def stop_checkpoint'))
end=s.index('\n    def pass_once',start)
s=s[:start]+'''        self.send(directory, marker, ['ckstop'])
        put(self.state/'ckstop.json', dict(status='gcs' if
            (self.state/('gcs_'+directory.name+'.done')).exists() else 'left node-local',
            marker_sha256=identity))

    def checkpoints(self):
        for marker in sorted(self.train.glob('checkpoint_*/complete.json')):
            self.attempt('checkpoint', lambda marker=marker: self.send(
                marker.parent, marker, ['ck%02d'%i for i in range(16)]))
''' + s[end:]
s=s.replace("                self.small()\n            for action in [self.exports]", "                self.attempt('small', self.small)\n            for action in [self.checkpoints, self.exports]")
s=s.replace("                    put(self.live/(action.__name__+'.json'), dict(status='pending retry', error=type(e).__name__))", "                    self.note(action.__name__, e)")
s=s.replace("            c.small()", "            c.attempt('small', c.small)").replace("        c.small()", "        c.attempt('small', c.small)")
s=s.replace("        c.pass_once(final=args.final, small=not args.loop)","        c.attempt('pass', lambda: c.pass_once(final=args.final, small=not args.loop))")
# Preflight copies and authenticates session mappings before training; no fallback to shared claims.
s=s.replace("        self.final_pass = False", """        self.final_pass = False
        private = self.spool/'private'
        private.mkdir(exist_ok=True, mode=0o700)
        cached = private/'sess.json'
        if not cached.exists():
            raw = self.session_bytes()
            values = json.loads(raw)
            expected = {key+'.j'+self.job+f'.part{i:02d}-of-04'
                        for key in self.names['objects'].values() for i in range(4)}
            if not expected.issubset(values):
                raise ValueError('E101')
            fd = os.open(cached, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream: stream.write(raw)
""")
s=s.replace('raw = self.session_bytes()\n        except ValueError',"raw = (self.spool/'private/sess.json').read_bytes()\n        except ValueError")
s=s.replace("    p.add_argument('--sessions')", "    p.add_argument('--sessions')\n    p.add_argument('--prepare', action='store_true')")
s=s.replace("    if args.small:", "    if args.prepare:\n        return\n    if args.small:")
(P/'b/pc.py').write_text(s)
s=(K/'b/pc.sh').read_text();s=s.replace("    python3 -B -I -s \"$ROOT/b/ep.py\"", "    python3 -B -I -s \"$ROOT/b/o.py\" \"$N\" \"$status\" 0 || true\n    python3 -B -I -s \"$ROOT/b/ep.py\"")
s=s.replace("trap 'tk_live_finish $?' EXIT", "python3 -B -I -s \"$ROOT/b/pc.py\" \"$ROOT\" \"$N\" \"$SLURM_JOB_ID\" --prepare\ntrap 'tk_live_finish $?' EXIT")
(P/'b/pc.sh').write_text(s)
s=(K/'b/o.py').read_text();s=s.replace(";out.mkdir(parents=True,exist_ok=True)",'')
s=s.replace("shutil.copyfile(local/'o.tar',out/'o.tar')\n",'')
s=s.replace("shutil.copyfile(local/'RESULT.json',out/'RESULT.json')",'''try:
 out.mkdir(parents=True,exist_ok=True)
 for name in ('o.tar','RESULT.json'):
  shutil.copyfile(local/name,out/(name+'.part'))
  os.replace(out/(name+'.part'),out/name)
except OSError as error:
 with (local/'retry.log').open('a') as stream:stream.write('E'+str(error.errno)+'\\n')''')
(P/'b/o.py').write_text(s)
# Exit diagnostics keep a local copy and errors local; the batch finalizer retries o.py.
s=(K/'b/ep.py').read_text();s=s.replace("    target.mkdir(parents=True,exist_ok=True,mode=0o700)","    target.mkdir(parents=True,exist_ok=True,mode=0o700)")
# Retry exit archive while allocation is alive, from the small publication worker.
s=(P/'b/pc.py').read_text();s=s.replace("        return total + len(raw)",'''        local = self.root/'o'
        for name in ('o.tar', 'RESULT.json'):
            source = local/name
            if source.is_file():
                destination = self.target/'o'/self.job/name
                partial = destination.with_name(name+'.part')
                shutil.copyfile(source, partial)
                os.replace(partial, destination)
        return total + len(raw)''')
(P/'b/pc.py').write_text(s)
y=json.loads((W/'decoded_y.json').read_text());key=y['objects']['ckstop'];prefix=key.rsplit('_',1)[0]
for i in range(16):y['objects']['ck%02d'%i]=prefix+'_ck%02d.tar'%i
raw=(json.dumps(y,sort_keys=True,separators=(',',':'))+'\n').encode();old=json.loads((K/'k/y.json').read_text());old['payload']=base64.b64encode(raw).decode();old['sha256']=hashlib.sha256(raw).hexdigest();(P/'k/y.json').write_text(json.dumps(old,sort_keys=True)+'\n')
files=['b/pc.py','b/pc.sh','b/o.py','k/y.json']
patch=''.join(''.join(difflib.unified_diff((K/n).read_text().splitlines(True),(P/n).read_text().splitlines(True),fromfile='a/out/kit_n_go/'+n,tofile='b/out/kit_n_go/'+n)) for n in files)
(J/'out/KIT_CHANGE_24M4Z.patch').write_text(patch)
for n in ('b/pc.py','b/o.py'):compile((P/n).read_text(),str(P/n),'exec')
print(files,len(patch))
