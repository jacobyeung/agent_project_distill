from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24g'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
kits={n:L/('out/kit_n_go' if n=='n_go' else 'work/build24/kits/'+n) for n in ('q','n','n_go')}
def hashes(k):return {str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
J.write(D/'BASELINE.json',dict(tree=inventory(L/'work/tree_r1'),kits={n:hashes(k) for n,k in kits.items()},packages={p.name:J.sha(p) for p in (L/'out').glob('*.tar')},session_names=J.sha(L/'out/SESSION_NAMES_24F.json')))
source=(kits['n']/'b/pc.py').read_text()
source=source.replace('import signal\n','import signal\nimport stat\nfrom urllib.parse import urlsplit\n')
source=source.replace('home=None, writer=None):','home=None, writer=None, sessions=None):')
source=source.replace("        self.home = Path(home or os.environ.get('TK_KIT_HOME', str(self.root/'h')))\n", "        self.sessions = Path(sessions) if sessions is not None else (Path(home)/'sess.json' if home is not None else Path(spec['n_root'])/'n_s/sess.json')\n        self.home = self.sessions.parent\n")
a=source.index("        sessions = self.home/'sess.json'",source.index('    def send('));b=source.index('        label, key = self.claim',a)
source=source[:a]+'''        archive = self.archive(directory, marker)
        try:
            raw = self.session_bytes()
        except ValueError as error:
            put(self.live/('gcs_'+directory.name+'.json'), dict(status='export not uploaded: sessions unusable ('+str(error)+')', archive=str(archive), marker_sha256=identity))
            return
'''+source[b:]
source=source.replace('        shutil.copyfile(sessions, local)\n        os.chmod(local, 0o600)\n', '''        os.chmod(private, 0o700)
        fd = os.open(local, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
''')
a=source.index('    def send(')
source=source[:a]+'''    def session_bytes(self):
        # Pin both opened objects; never follow a replaced directory or file link.
        directory = None
        try:
            try:
                directory = os.open(self.sessions.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            except FileNotFoundError:
                raise ValueError('directory missing') from None
            except OSError:
                raise ValueError('directory inaccessible') from None
            info = os.fstat(directory)
            if info.st_uid != os.getuid():
                raise ValueError('directory owner')
            if stat.S_IMODE(info.st_mode) != 0o700:
                raise ValueError('directory mode')
            try:
                info = os.stat(self.sessions.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                raise ValueError('file missing') from None
            if stat.S_ISLNK(info.st_mode):
                raise ValueError('file symlink')
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('file not regular')
            fd = os.open(self.sessions.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, 'rb') as stream:
                current = os.fstat(stream.fileno())
                if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                    raise ValueError('file changed')
                if stat.S_IMODE(current.st_mode) != 0o600:
                    raise ValueError('file mode')
                raw = stream.read()
            try:
                values = json.loads(raw)
            except (ValueError, UnicodeError):
                raise ValueError('invalid JSON') from None
            if not isinstance(values, dict):
                raise ValueError('not an object')
            for name, value in values.items():
                if not isinstance(name, str) or not name or not isinstance(value, str):
                    raise ValueError('invalid mapping')
                try:
                    url = urlsplit(value)
                    valid = url.scheme in ('http', 'https') and bool(url.netloc)
                except ValueError:
                    valid = False
                if not valid:
                    raise ValueError('invalid URL')
            return raw
        except OSError:
            raise ValueError('file inaccessible') from None
        finally:
            if directory is not None:
                os.close(directory)

'''+source[a:]
source=source.replace('    args = p.parse_args()', "    p.add_argument('--sessions')\n    args = p.parse_args()")
source=source.replace('c = Copier(args.kit,args.root,args.job)','c = Copier(args.kit,args.root,args.job,sessions=args.sessions)')
(D/'live.py').write_text(source)
(D/'live.sh').write_bytes((L/'work/build24f/live.sh').read_bytes())
for p in (L/'work/build24f/live.py',kits['n']/'b/pc.py',kits['n_go']/'b/pc.py'):
    old=L/'attic/build24g'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True);p.rename(old);p.write_text(source)
for name in ('checks','kit_tests','naming_tests','resolver_tests','resolver600_tests','resolver23_tests','guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','suites'):
    s=(L/'work/build24f'/(name+'.py')).read_text().replace('work/build24f','work/build24g').replace('naming24f_','naming24g_')
    (D/(name+'.py')).write_text(s)
for n in ('n','q'):(D/('guard_'+n)).mkdir()
s=(L/'work/build24f/live_tests.py').read_text().replace('work/build24f','work/build24g')
s=s.replace('home.mkdir()','home.mkdir(mode=0o700)')
s=s.replace("C.put(c.home/'sess.json',{})","C.put(c.home/'sess.json',{});os.chmod(c.home/'sess.json',0o600)")
s=s.replace('export not uploaded: no sessions','export not uploaded: sessions unusable (file missing)')
(D/'live_tests.py').write_text(s)
s=(L/'work/build24f/uploads.py').read_text().replace('work/build24f','work/build24g').replace('build24f-','build24g-').replace('UPLOADS_24F_GO','UPLOADS_24G_GO').replace('UPLOADS_24F.list','UPLOADS_24G.list').replace('UPLOADS_24F.json','UPLOADS_24G.json')
s=s.replace("'UPLOADS_24D.json','UPLOADS_24E.json')","'UPLOADS_24D.json','UPLOADS_24E.json','UPLOADS_24F.json')")
(D/'uploads.py').write_text(s)
print('Prepared isolated build24g harness and copiers')
