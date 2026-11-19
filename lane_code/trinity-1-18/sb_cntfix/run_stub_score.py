from pathlib import Path
import sys,time,os
os.environ["COUNT_STUB_NAMESPACE"]="final"
sys.path.insert(0,'kit/files')
import count_guard as G
import score_count_pricing as S
m=Path('out/MANIFEST_R0DEV.json')
G.register(m,None,True,time.time()+1800,1800)
S.dev_read('kit/files/COUNT_ITEMS_535.jsonl','out/stub_final','out/STUB_SCORE.json','R0-dev',str(m),stub=True)
try:S.dev_read('kit/files/COUNT_ITEMS_535.jsonl','out/stub_final','out/REPEATED_STUB_SCORE.json','R0-dev',str(m),stub=True)
except FileExistsError:
 G.write('out/STUB_REPLAY_TEST.json',dict(rejected=True,second_output_exists=Path('out/REPEATED_STUB_SCORE.json').exists(),inputs_sha256={str(m):G.sha(m),str(__file__):G.sha(__file__),**G.pins()}));print('repeated score across output paths rejected')
else:raise AssertionError('duplicate score allowed')
