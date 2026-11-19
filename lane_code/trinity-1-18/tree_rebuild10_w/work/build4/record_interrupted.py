import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/build4/package_1794786224789770885'
lines=(p/'proof/tests.log').read_text().splitlines()
done=[s for s in lines if ' ... ' in s and s.rsplit(' ... ',1)[1].startswith(('ok','FAIL','ERROR','skipped'))]
result=dict(tests=None,completed_from_log=len(done),exit_code=130,
    failures=sum(s.endswith('FAIL') for s in done),errors=sum(s.endswith('ERROR') for s in done),
    skips=sum(' ... skipped' in s for s in done),all_tree_tests=True,
    fatal='Builder interrupted to forbid unaudited child processes; this was not a cluster kill.',
    evidence=str((p/'proof/tests.log').relative_to(L)),archive=str((p/'package.tar.gz').relative_to(L)))
(p/'PACKAGE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
