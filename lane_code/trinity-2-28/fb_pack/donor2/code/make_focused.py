from pathlib import Path
import json
W=Path(__file__).resolve().parents[1]
d=json.loads((W.parent/'donorrev/work/suite_new.json').read_text());names=sorted({'.'.join(k.split('.')[:2]) for k in d if k.startswith('tests.')})
s=(W/'code/run_suite_final.py').read_text().replace("dest=W/'work'/('suite_final_'+sys.argv[1])", "dest=W/'work'/('focused_'+sys.argv[1])")
s=s.replace("for path in sorted((tree/'tests').rglob('test*.py')):", "names="+repr(names)+"\nif (tree/'tests/test_host24j.py').exists():names.append('tests.test_host24j')\nfor path in [tree.joinpath(*name.split('.')).with_suffix('.py') for name in names if name!='tests.test_scale_donor' or (tree/'tests/test_scale_donor.py').exists()]:")
s=s.replace("'SUITE_'+sys.argv[1].upper()+'_FINAL.json'", "'FOCUSED_'+sys.argv[1].upper()+'.json'").replace('code/run_suite_final.py ', 'code/run_focused.py ')
(W/'code/run_focused.py').write_text(s)
