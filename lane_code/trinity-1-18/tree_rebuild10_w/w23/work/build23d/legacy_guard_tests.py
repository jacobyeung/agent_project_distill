from pathlib import Path
L=Path(__file__).resolve().parents[2]
source=(L/'work/build23c/guard_tests.py').read_text()
# Retain all nine cases; adapt only output location and the changed diagnostic schema.
source=source.replace("D=L/'work/build23c'","D=L/'work/build23d'")
source=source.replace("{'v','a','c','e','n','m','d0','dc','x'}","{'v','a','c','e','ec','n','m','d0','dc','x'}")
source=source.replace("diag['e']=='0'","diag['e'] is True and diag['ec']==1")
source=source.replace("D/'GUARD_TESTS.json'","D/'LEGACY_GUARD_TESTS.json'")
exec(compile(source,str(L/'work/build23c/guard_tests.py'),'exec'),{'__file__':str(L/'work/build23c/guard_tests.py'),'__name__':'__main__'})
