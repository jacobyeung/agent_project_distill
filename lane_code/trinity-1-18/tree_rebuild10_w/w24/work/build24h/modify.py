from pathlib import Path
import sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24h'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J

def replace(p,s):
 old=L/'attic/build24h'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 if not old.exists():p.rename(old)
 p.write_text(s)

source=(L/'out/kit_n_go/b/pc.py').read_text()
a=source.index('        self.target =');b=source.index('        self.final_pass = False',a)
source=source[:a]+'''        self.target = Path(spec['n_root']).absolute()
        self.job = str(job)
        if not self.job.replace('_', '').isalnum():
            raise ValueError('E91')
        self.live = self.target/'o'/self.job/'live'
        self.claims = self.target/'o'/'gcs_claims'
        self.checkpoint = self.target/'n_ck'/self.job
        self.spool = self.root/'live_spool'
        self.train = Path(train) if train else self.root/'r'
        self.sessions = Path(sessions) if sessions is not None else (Path(home)/'sess.json' if home is not None else self.target/'n_s/sess.json')
        self.home = self.sessions.parent
        self.writer = Path(writer) if writer else self.kit/'b/gc.py'
        self.names = read(self.kit/'k/y.json')
        if target is not None and Path(target).absolute() != self.target:
            raise ValueError('R1_COPY_TARGET_OUTSIDE_N_ROOT')
        self.paths()
        self.live.mkdir(parents=True, exist_ok=True)
        self.spool.mkdir(parents=True, exist_ok=True)
        self.claims.mkdir(parents=True, exist_ok=True)
'''+source[b:]
a=source.index('    def small(self):')
source=source[:a]+'''    def paths(self):
        # Validate before the first mkdir and every pass. Reject symlink ancestors.
        forbidden = (self.kit, self.root/'kit', self.root/'h')
        for name, path, expected in (
            ('LIVE', self.live, self.target/'o'/self.job/'live'),
            ('CLAIMS', self.claims, self.target/'o/gcs_claims'),
            ('N_CK', self.checkpoint, self.target/'n_ck'/self.job),
            ('SESSIONS', self.sessions, self.target/'n_s'/self.sessions.name)):
            absolute = path.absolute()
            resolved = path.resolve()
            if any(resolved == p.resolve() or resolved.is_relative_to(p.resolve()) for p in forbidden):
                raise ValueError('R1_COPY_'+name+'_INSIDE_KIT')
            if absolute != expected or not absolute.is_relative_to(self.target) or '..' in path.parts:
                raise ValueError('R1_COPY_'+name+'_OUTSIDE_N_ROOT')
            # The session leaf is checked by session_bytes for its named status.
            probe = absolute.parent if name == 'SESSIONS' else absolute
            if any(p.is_symlink() for p in (probe, *probe.parents)):
                raise ValueError('R1_COPY_'+name+'_PATH_SYMLINK')
        if self.root == self.kit or self.root.is_relative_to(self.kit):
            raise ValueError('R1_COPY_ROOT_INSIDE_KIT')
        if self.spool.is_symlink() or self.spool.resolve().is_relative_to(self.kit):
            raise ValueError('R1_COPY_SPOOL_INSIDE_KIT')

'''+source[a:]
source=source.replace("    def small(self):\n", "    def small(self):\n        self.paths()\n")
source=source.replace("    def pass_once(self, final=False, small=True):\n", "    def pass_once(self, final=False, small=True):\n        self.paths()\n")
source=source.replace("        destination = self.target/'n_ck'/self.job", "        self.paths()\n        destination = self.checkpoint")
source=source.replace('            self.send(marker.parent, marker, labels)', '''            try:
                self.send(marker.parent, marker, labels)
            except Exception as error:
                put(self.live/('gcs_'+marker.parent.name+'.json'),
                    dict(status='pending retry', error=type(error).__name__))''')
# A stopped loop must not run final while the trainer still writes.
source=source.replace('                c.pass_once(final=True,small=False)\n                return','                return')
(D/'live.py').write_text(source)
for name in ('n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/n')
 replace(k/'b/pc.py',source)
 s=(k/'job.sh').read_text().replace('source "$ROOT/b/pc.sh"\n','')
 line='python3 -B -I -s -B "$ROOT/b/v.py" "$ROOT"'
 s=s.replace(line,line+'\nsource "$ROOT/b/pc.sh"')
 old='python3 -B -I -s -B "$ROOT/b/x.py" "$ROOT" "$R" "$N" 2>&1 | python3 -B -I -s -B "$ROOT/b/l.py" "$ROOT" &'
 new='( python3 -B -I -s -B "$ROOT/b/x.py" "$ROOT" "$R" "$N" 2>&1 | python3 -B -I -s -B "$ROOT/b/l.py" "$ROOT" ) &'
 assert old in s;s=s.replace(old,new)
 replace(k/'job.sh',s)
print('copier guards and per-export recovery installed')
