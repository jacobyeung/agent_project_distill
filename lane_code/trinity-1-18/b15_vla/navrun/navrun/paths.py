from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'out'
INPUTS = ROOT.parent / 'navrun_inputs'
RAND100 = INPUTS / 'rand100/OpenNav_R2R-CE_100_bertidx.json.gz'
R2R = INPUTS / 'refs/r2r_vlnce/R2R_VLNCE_v1-3'
R2R_GT = INPUTS / 'refs/r2r_vlnce_preprocessed/R2R_VLNCE_v1-3_preprocessed'
R2RIE = INPUTS / 'refs/r2rie/R2RIE_CE_1_3_v1'
SCENES = INPUTS / 'scenes/mp3d'
CODEC = ROOT.parent / 'work/orchard_kit/kit/ext_v2/vla_heads/vla_heads/codecs/nav_text.py'
