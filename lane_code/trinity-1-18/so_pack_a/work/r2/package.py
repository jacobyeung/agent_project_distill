from pathlib import Path
import difflib, hashlib, json, subprocess, sys
r=Path(__file__).parent;root=r.parent.parent;src=r/'src';out=root/'out'
inp=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
files=sorted([str(p.relative_to(src)) for p in src.glob('*.py')]+[str(p.relative_to(src)) for p in (src/'out').iterdir() if p.is_file() and p.name!='REPORT.md'])
hashes={}
for name in files:
    assert not (inp/name).exists(),name
    data=(src/name).read_bytes();dest=root/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
def added(name,text):return ''.join(difflib.unified_diff([],text.splitlines(True),fromfile='/dev/null',tofile='b/'+name))
(out/'patches/01_read_package.diff').write_text(''.join(added(n,(src/n).read_text()) for n in files))
adapters={}
for parent in ['cont_ops17/work','cont_ops18/dbuild']:
    for name in ['pack_token.py','test_pack_token.py']:
        target=parent+'/'+name;assert not (inp/target).exists();adapters[target]=hashes[name]
(out/'patches/02_opt_in_token.diff').write_text(''.join(added(n,(src/Path(n).name).read_text()) for n in adapters))
applied=r/(sys.argv[1] if len(sys.argv)>1 else 'applied');applied.mkdir()
for name in ['cont_ops17/work/build_r10.py','cont_ops18/dbuild/build_d.py','cont_ops18/dbuild/o_build_D.sh']:
    p=applied/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((inp/name).read_bytes())
logs=[]
for patch in ['01_read_package.diff','02_opt_in_token.diff']:
    cmd=['nice','-n','10','patch','--batch','-p1','--directory',str(applied),'--input',str(out/'patches'/patch)]
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);assert result.returncode==0,result.stdout.decode();logs.append(result.stdout.decode())
for name,h in dict(hashes,**adapters).items():assert hashlib.sha256((applied/name).read_bytes()).hexdigest()==h,name
(r/'patch_apply.log').write_text(''.join(logs))
(out/'TOOL_SHA256.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n')
(r/'PATCH_BASE.json').write_text(json.dumps(dict(canonical=hashes,adapter_copies=adapters,applied=str(applied),source_unchanged={n:hashlib.sha256((inp/n).read_bytes()).hexdigest() for n in ['cont_ops17/work/build_r10.py','cont_ops18/dbuild/build_d.py','cont_ops18/dbuild/o_build_D.sh']}),sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(passed=True,canonical_files=len(hashes),adapter_copies=len(adapters),patch_sizes={n:(out/'patches'/n).stat().st_size for n in ['01_read_package.diff','02_opt_in_token.diff']}),sort_keys=True))
