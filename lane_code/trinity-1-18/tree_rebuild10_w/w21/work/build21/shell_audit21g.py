"""Record the reviewed fixed-key shell programs; never run during a kit scan.

The allowlist is bound to complete source bytes, not to a filename or prefix.
The inherited wrapper uses fixed read/for/local names, fixed export names and a
bwrap argv array. Its only embedded Python writes files, not environments.
Every source token still goes through the independent forbidden-name scanner.
"""
from pathlib import Path
import base64,hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build21';K=B/'kits/q'
records={}
for path in [*sorted(K.rglob('*.sh')),K/'k/j.json']:
    source=path.read_text()
    if path.suffix=='.json':source=base64.b64decode(json.loads(source)['payload']).decode()
    bindings=[]
    for number,line in enumerate(source.splitlines(),1):
        names=set(re.findall(r'(?<![\w$])([A-Za-z_]\w*)=(?!=)',line))
        loop=re.search(r'\bfor\s+([A-Za-z_]\w*)\s+in\b',line)
        if loop:names.add(loop.group(1))
        read=re.search(r'\bread -r ([A-Za-z_][\w ]*)',line)
        if read:names.update(read.group(1).split())
        local=re.search(r'^\s*local ([A-Za-z_][\w ]*)$',line)
        if local:names.update(local.group(1).split())
        export=re.search(r'\bexport ([A-Z_][A-Z_0-9]*)(?: |$)',line)
        if export:names.add(export.group(1))
        if names:bindings.append(dict(line=number,names=sorted(names),expression=line))
    records[str(path.relative_to(K))]=dict(sha256=hashlib.sha256(source.encode()).hexdigest(),
        runtime_literal_names=sorted({k for row in bindings for k in row['names']}),bindings=bindings,
        reason='Fixed identifier assignments, exports, read targets and loop targets in this exact reviewed program; runtime path/input values are allowed only for these names. No computed environment key or indirect export occurs.')
target=B/'environment_shell21g.json'
assert not target.exists()
target.write_text(json.dumps(records,indent=2)+'\n')
