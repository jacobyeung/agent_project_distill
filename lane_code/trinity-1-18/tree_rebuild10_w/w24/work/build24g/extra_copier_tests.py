from pathlib import Path
import importlib.util,json,os,stat,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24g'
sys.path.insert(0,str(D))
import live as C
from live_tests import WRITER
root=D/'extra_copier';root.mkdir()
kit=root/'kit';(kit/'k').mkdir(parents=True);(kit/'b').mkdir()
node=root/'node';node.mkdir();target=root/'project';target.mkdir()
C.put(kit/'k/p.json',dict(n_root=str(target)))
C.put(kit/'k/n.json',{})
C.put(kit/'k/y.json',dict(objects={'m100':'q9/test/m100.tar'}))
writer=kit/'b/gc.py'
token='https://'+'example.invalid/'+os.urandom(16).hex()
sd=target/'n_s'
sd.mkdir(mode=0o700)
c=C.Copier(kit,node,'51')
export=c.train/'m100';export.mkdir(parents=True)
(export/'w.bin').write_bytes(b'fixture')
C.put(export/'artifact.json',dict(step=100))
c.exports()
assert C.read(c.live/'gcs_m100.json')['status']=='export not uploaded: sessions unusable (file missing)'
sessions=sd/'sess.json'
values={f'q9/test/m100.tar.part{i:02d}-of-04':token+str(i) for i in range(4)}
sessions.write_text(json.dumps(values));sessions.chmod(0o600)
# The writer emits a capability-bearing error; all diagnostics must be discarded.
writer.write_text("import json,sys\nfrom pathlib import Path\nprint(next(iter(json.loads(Path(sys.argv[2]).read_text()).values())))\nraise SystemExit(1)\n")
c.exports()
assert C.read(c.live/'gcs_m100.json')['status']=='upload pending retry'
assert not (c.live/'gcs_m100.done').exists()
writer.write_text(WRITER.replace("out=Path(s).parent", "assert all(key+f'.part{i:02d}-of-04' in json.loads(Path(s).read_text()) for i in range(4))\nout=Path(s).parent"))
c.exports()
assert (c.live/'gcs_m100.done').is_file()
for p in c.live.rglob('*'):
    if p.is_file():assert token.encode() not in p.read_bytes()
assert stat.S_IMODE((c.spool/'private/sess.json').stat().st_mode)==0o600
# The directory itself may not be a symlink, even to a correctly protected target.
linked=root/'linked';linked.symlink_to(sd,target_is_directory=True)
override=C.Copier(kit,node,'52',sessions=linked/'sess.json')
override.exports()
assert C.read(override.live/'gcs_m100.json')['status']=='export not uploaded: sessions unusable (directory inaccessible)'
missing=C.Copier(kit,node,'53',sessions=root/'absent/sess.json')
missing.exports()
assert C.read(missing.live/'gcs_m100.json')['status']=='export not uploaded: sessions unusable (directory missing)'
assert not list(override.live.glob('*.done')) and not list(missing.live.glob('*.done'))
(D/'EXTRA_COPIER_TESTS.json').write_text(json.dumps(dict(status='PASS',late_mint_retry=True,writer_failure_redacted=True,four_part_mapping=True,directory_symlink_refused=True,directory_missing_refused=True),indent=2)+'\n')
print('PASS: late mint, noisy writer failure, four parts, directory symlink and missing directory')
