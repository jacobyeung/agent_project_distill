from pathlib import Path
import hashlib
pins={'/project/community/jjyeung/okh7/e6fc152498/g/0': 5627176960, '/project/community/jjyeung/okh7/e6fc152498/a2.tar': 5257369600, '/project/community/jjyeung/okh7/e6fc152498/a4.tar': 145274880, '/project/community/jjyeung/okh7/e6fc152498/a3.tar': 10240, '/project/community/jjyeung/okh7/af83c921/d81f4a26.tar': 797685760, '/home/jjyeung/okit/p/d59945c1/4fe70504.00': 900000000, '/home/jjyeung/okit/p/d59945c1/4fe70504.01': 721422080, '/home/jjyeung/okit/p/d59945c1/50011a59.00': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.01': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.02': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.03': 900000000, '/home/jjyeung/okit/p/d59945c1/50011a59.04': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08': 900000000, '/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09': 366728960, '/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00': 409282560, '/project/community/jjyeung/cp4tk_rt/kit/bwrap': 72160, '/project/community/jjyeung/okh7/eabcdef012345/5': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/6': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/7': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/8': 5395758080, '/project/community/jjyeung/okh7/eabcdef012345/9': 101, '/project/community/jjyeung/okh7/eabcdef012345/10': 243, '/project/community/jjyeung/okh7/eabcdef012345/11': 121, '/project/community/jjyeung/okh7/eabcdef012345/12': 401}
for name,size in pins.items():
 p=Path(name)
 if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)
done=Path('/project/community/jjyeung/okh7/eabcdef012345/9')
if done.stat().st_size>4096 or done.read_text().split()!=['q8/8865619b/673bc60f_m200.tar', '21583032320', '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b']:raise ValueError('Reviewed whole-tar receipt differs: '+str(done))
for name,sha in {'/project/community/jjyeung/okh7/eabcdef012345/10': '3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1', '/project/community/jjyeung/okh7/eabcdef012345/11': '4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915', '/project/community/jjyeung/okh7/eabcdef012345/12': '7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770'}.items():
 p=Path(name)
 if p.stat().st_size>1048576:raise ValueError('Preparation input exceeds metadata budget: '+name)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Reviewed preparation differs: '+name)
import hashlib,json,os,stat,tarfile
from pathlib import Path
def stamp(p):
 s=p.stat()
 if not stat.S_ISREG(s.st_mode):raise ValueError('Export part is not a regular file: '+str(p))
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino)
def header(path,member):
 with Path(path).open('rb') as stream:raw=stream.read(512)
 entry=tarfile.TarInfo.frombuf(raw,'utf-8','strict')
 name=entry.name.rstrip('/')
 if name!=member and not name.startswith(member+'/'):raise ValueError('Export tar member differs: '+name)
 if '..' in name.split('/') or entry.type not in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE):raise ValueError('Unsupported export tar header')
p=Path('/project/community/jjyeung/okh7/a15_cot_apb123456789abc')/'v';identity={'done': ['q8/8865619b/673bc60f_m200.tar', '21583032320', '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'], 'preparation': {'/project/community/jjyeung/okh7/eabcdef012345/10': '3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1', '/project/community/jjyeung/okh7/eabcdef012345/11': '4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915', '/project/community/jjyeung/okh7/eabcdef012345/12': '7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770'}, 'parts': [{'path': '/project/community/jjyeung/okh7/eabcdef012345/5', 'bytes': 5395758080, 'sha256': '54c5c16ae8100ec501b2c6e650efa998a488db05afb7c9a4341defb9593730cf'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/6', 'bytes': 5395758080, 'sha256': '028aaee51b02d1265cc05d3ab2057625a14a4178429f1e2840301b1e77cc299a'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/7', 'bytes': 5395758080, 'sha256': '500f0643c46e7511e66e553766dcff4c6836ae02c997c6abbc51cc36cdffa9b2'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/8', 'bytes': 5395758080, 'sha256': '67988559d896dc33363066b6c89d3cb17479e6c8c93f11f978013f7d4a647dc8'}], 'member_directory': 'm200'}
if not (p/'0.txt').is_file() or not (p/'0.json').is_file():raise ValueError('Export verification receipt missing; run verify before place')
if (p/'0.txt').read_text()!='0\n':raise ValueError('Export verification incomplete')
if (p/'0.json').stat().st_size>16384:raise ValueError('Export verification receipt too large')
receipt=json.loads((p/'0.json').read_text())
if receipt.get('schema')!=1 or len(receipt.get('parts',[]))!=4:raise ValueError('Export verification receipt invalid')
for row,pin in zip(receipt['parts'],identity['parts']):
 if any(row.get(k)!=pin[k] for k in ('path','bytes','sha256')):raise ValueError('Export verification receipt differs from binding')
 if any(row.get(k)!=v for k,v in stamp(Path(pin['path'])).items()):raise ValueError('Export verification receipt is stale: '+pin['path'])
header(identity['parts'][0]['path'],identity['member_directory'])
print('inputs ready')

