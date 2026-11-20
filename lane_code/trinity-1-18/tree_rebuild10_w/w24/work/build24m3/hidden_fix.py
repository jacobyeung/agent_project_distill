from common import *
s=(D/'hidden_resume.py').read_text()
s=s.replace(" shutil.copytree(kit(name),k,copy_function=transport)"," if not k.exists():shutil.copytree(kit(name),k,copy_function=transport)")
s=s.replace("  if not p.exists():p=base/'target/u'/h","  if not p.exists():p=base/'target/u'/h\n  if not p.exists():p=Path(J.load(L/'work/build24m2c/PIN_AUDIT.json')['available'][h])")
s=s.replace("u.mkdir(parents=True)","u.mkdir(parents=True,exist_ok=True)")
(D/'hidden_final.py').write_text(s)
