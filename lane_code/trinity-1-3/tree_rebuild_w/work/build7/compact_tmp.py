"""Replace completed scratch products in place with bounded digest receipts."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

inventory_root=None


def native_inventory(root):
    """Use a read-only C walker; retain exactly the Python census's file sizes."""
    result = subprocess.run(['/usr/bin/find', str(root), '-type', 'f', '-printf', r'%s\t%p\0'],
                            capture_output=True, check=True)
    values = {}
    for record in result.stdout.split(b'\0'):
        if record:
            size, path = record.split(b'\t', 1)
            values[os.fsdecode(path)] = int(size)
    return values

def inventory(root):
    global inventory_root
    root=Path(root).resolve()
    result={}
    pending=[str(root)]
    inventory_root=str(root)
    try:
        if os.environ.get('R2_FAST_CENSUS') == '1':
            return native_inventory(root)
        while pending:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    if entry.is_symlink():continue
                    if entry.is_dir(follow_symlinks=False):pending.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):result[entry.path]=entry.stat(follow_symlinks=False).st_size
    finally:inventory_root=None
    return result

def compact(root, protected=(), preserved_files=(), files=None, package_files=None):
    if package_files is None:protected = (*protected, Path(root)/'package')
    else:preserved_files=set(preserved_files)|set(package_files)
    preserved_files={str(p) for p in preserved_files}
    records=[]
    files=inventory(root) if files is None else files
    candidates=((Path(p),size) for p,size in files.items() if size>512 and str(p) not in preserved_files)
    for p,size in sorted((p,size) for p,size in candidates
                         if not any(q==p or q in p.parents for q in protected)):
        h=hashlib.sha256()
        with p.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        row=dict(bytes=size,sha256=h.hexdigest())
        mode=p.stat().st_mode
        if not mode & 0o200:p.chmod(mode|0o200)
        p.write_text(json.dumps(dict(completed_scratch_product=row))+'\n')
        if not mode & 0o200:p.chmod(mode)
        records.append(dict(path=str(p),**row))
    return records

if __name__=='__main__':
    L=Path(__file__).resolve().parents[2]
    rows=compact(L/'work/tmp')
    (L/'work/build7/TMP_COMPACTION.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(dict(overwritten=len(rows),original_bytes=sum(r['bytes'] for r in rows))))
