from pathlib import Path
import shutil,json
L=Path.cwd();D=L/"work/build24m4y";source=L/"work/build24m4u/assets2"
records={str(p.relative_to(source)):p.stat().st_size for p in source.rglob("*") if p.is_file()}
assert sum(records.values())<50_000_000
shutil.copytree(source,D/"assets2")
print(json.dumps(dict(files=len(records),bytes=sum(records.values()))))
