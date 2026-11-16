import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HERE=ROOT.parent/'kc_guard/k1_build/work/kit_k1a/native_kit'
name=sys.argv[1]
assert name in ('test_kit','test_guards')
p=HERE/(name+'.py')
s=p.read_text()
# Relocate only test artifact constants in memory; source files stay byte-identical.
s=s.replace("ROOT=LANE/'work'/('tests_'", "ROOT=TEST_ROOT/('tests_'")
s=s.replace("ROOT=HERE.parent/'work'/('guards_'", "ROOT=TEST_ROOT/('guards_'")
s=s.replace("LANE/'out/", "TEST_ROOT/'")
s=s.replace("HERE.parent/'out/", "TEST_ROOT/'")
ns=dict(__name__='__main__',__file__=str(p),TEST_ROOT=ROOT)
exec(compile(s,str(p),'exec'),ns)
