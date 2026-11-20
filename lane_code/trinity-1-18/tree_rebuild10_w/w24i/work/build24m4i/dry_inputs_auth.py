import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
cfg=J.load(D/'P_CONFIG.json')
prep=input_file(cfg['preparation']['sha256']);receipt=J.load(prep)
assert receipt==J.load(D/'P_preparation.json')
tm=input_file(receipt['type_mix_population']['sha256']);assert J.load(tm)==J.load(D/'P_type_mix.json')
replace(D/'P_preparation.json',prep.read_bytes());replace(D/'P_type_mix.json',tm.read_bytes())
print(prep,tm)
