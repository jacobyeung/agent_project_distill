from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
if (B/'kits').exists():
    (B/'kits').rename(B/'retained_kits_attempt')
