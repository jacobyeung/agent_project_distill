import ast,hashlib,io,json,tarfile
from pathlib import Path
B=Path(__file__).resolve().parents[1]
S=B/'out/c8/sources'
data=io.BytesIO()
with tarfile.open(fileobj=data,mode='w',format=tarfile.USTAR_FORMAT) as archive:
    for p in sorted(S.rglob('*')):
        if not p.is_file():continue
        name=str(p.relative_to(S));content=p.read_bytes()
        info=tarfile.TarInfo(name);info.size=len(content)
        info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
        info.mode=0o755 if name.endswith(('/vnice/vnice.sh','/vnice/terminator.sh')) else 0o644
        archive.addfile(info,io.BytesIO(content))
expected=hashlib.sha256((B/'out/c8/code_c8.tar').read_bytes()).hexdigest()
assert hashlib.sha256(data.getvalue()).hexdigest()==expected
count=0
for root in (B/'out/tests',B/'out/rehearsal',B/'work'):
    for path in root.glob('*.py'):
        ast.parse(path.read_text(),filename=str(path));count+=1
value=dict(archive_rebuild_sha256=expected,byte_identical=True,helper_syntax_files=count,
           bytes_owned=sum(p.stat().st_size for p in B.rglob('*') if p.is_file() and not p.is_symlink()))
assert value['bytes_owned']<2500000000
(B/'out/PACKAGE_VERIFICATION.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
