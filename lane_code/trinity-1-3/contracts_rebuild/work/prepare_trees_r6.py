from pathlib import Path
import shutil,subprocess,sys,tarfile,json
L=Path(__file__).resolve().parents[1];B=L/'work/base/work/base/tree_b01ce449'
# Reuse the sealed baseline directly in render harnesses.
for p in (L/'work/row_families_r6').glob('*.py'):
    s=p.read_text().replace("L/'work/trees'/('r6_base' if args.arm == 'base' else 'r6_applied')", "L/'work/base/work/base/tree_b01ce449' if args.arm == 'base' else L/'work/trees/r6_applied'")
    s=s.replace("L/'work/trees'/('r6_base' if arm=='base' else 'r6_applied')", "L/'work/base/work/base/tree_b01ce449' if arm=='base' else L/'work/trees/r6_applied'")
    p.write_text(s)
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build_packet_r6.py')],check=True)
T=L/'work/trees/r6_applied';shutil.copytree(B,T)
for p in [T,*T.rglob('*')]:p.chmod(p.stat().st_mode|0o200)
R=L/'work/trees/r6_snapshot';R.mkdir()
with tarfile.open(L/'work/tree_r1/tree_r1_build1_fab2eea8.tar') as t:
    for m in t:
        parts=Path(m.name).parts
        if len(parts)<2:continue
        d=R/Path(*parts[1:])
        if m.isdir():d.mkdir(parents=True,exist_ok=True)
        else:
            assert m.isfile();d.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as a,d.open('wb') as b:shutil.copyfileobj(a,b)
proof={}
for key,target in [('base',T),('tree_r1',R)]:
    def run(args):
        p=subprocess.run(args,capture_output=True,text=True)
        return dict(command=list(map(str,args)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    cmd=['bash',str(L/'out/apply_contract_patches_r6.sh'),str(target)]
    dry=run(cmd+['--dry-run']);assert dry['returncode']==0,dry
    apply=run(cmd);assert apply['returncode']==0,apply
    repeat=run(cmd);assert repeat['returncode']!=0,repeat
    proof[key]=dict(tree=str(target),dry=dry,apply=apply,repeat=repeat)
(L/'out/APPLY_PROOF_R6.json').write_text(json.dumps(proof,indent=2)+'\n')
