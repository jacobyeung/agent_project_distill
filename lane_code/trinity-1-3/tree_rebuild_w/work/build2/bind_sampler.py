from pathlib import Path
L=Path(__file__).resolve().parents[2]
path=L/'work/tree_r1/student_pilot/carrier_c1_run.py'
text=path.read_text()
text=text.replace("mix=recipe['mix'],world=recipe['world_size'])", "mix=recipe['mix'],world=recipe['world_size'],r2_sampling=cfg.get('r2_sampling'))")
path.write_text(text)
