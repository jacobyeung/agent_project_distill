from pathlib import Path
p=Path(__file__).resolve().parents[2]/'work/tree_r1/student_pilot/carrier_c1_run.py'
s=p.read_text()
s=s.replace("r2_sampling=cfg.get('r2_sampling')", "r2_sampling=cfg.get('r2_sampling'),require_r2='r2_identity' in cfg")
p.write_text(s)
