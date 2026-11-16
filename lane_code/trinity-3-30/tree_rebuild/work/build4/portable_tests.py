from pathlib import Path
import re
L=Path(__file__).resolve().parents[2]
for p in (L/'work/tree_r1/tests').glob('test_r2*.py'):
    s=p.read_text()
    if "LANE/'out/" in s:
        if p.name != 'test_r2_data_path.py':
            s=s.replace('from tests.test_r2_data_path import ', 'from tests.test_r2_data_path import PROOFS, ')
        s=s.replace("LANE/'out/B3_BANK_ENTRYPOINTS.json'", "LANE/'references/B3_BANK_ENTRYPOINTS.json'")
        s=s.replace("LANE/'out/", "PROOFS/'")
    s=s.replace("LANE/'work/tree_r1/", "Path(__file__).resolve().parents[1]/'")
    p.write_text(s)
