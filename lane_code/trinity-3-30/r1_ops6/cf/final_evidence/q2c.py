import json, re
from cd_load import load, load_on16k
D, _ = load(); O, _ = load_on16k()
F = json.load(open('Q2_FORMS.json'))
def short(t, n=420):
    t = (t or '').replace('\n', ' | ')
    return t if len(t) <= n else t[:n] + f' ...[{len(t)} chars]'
picked = []
cats = [('dev-S1', lambda x: x['forced'] and 'REGION' not in x['tags']),
        ('dev-S1', lambda x: x['forced'] and 'REGION' in x['tags']),
        ('dev-S1', lambda x: (not x['forced']) and x['pf'] == 'FS_LIST' and x['ls'] and x['ls']['dup'] > 0),
        ('R0-dev', lambda x: x['forced'] and not x['multi'] and 'SECONDS' not in x['tags']),
        ('R0-dev', lambda x: x['forced'] and 'SECONDS' in x['tags']),
        ('R0-dev', lambda x: (not x['forced']) and not x['multi'] and x['pf'] == 'FS_LIST' and x['ls'] and x['ls']['dup'] > 0)]
L = []
for s, f in cats:
    rows = [x for x in F[f'R1m100|{s}'] if f(x)]
    B = D['S544'][s]
    rows.sort(key=lambda x: (-(float(B[x['id']]['score']) - x['score']), x['id']))
    x = rows[0]; i = x['id']
    b16 = O['S544'][s][i]; r16 = O['R1m100'][s][i]; d16 = O['D0m100'][s][i]
    L.append(f"### {s} item {i} (room {B[i]['room']}): {B[i]['question']}  GT {B[i]['ground_truth']}")
    L.append(f"- step 544: answer {B[i]['extracted_answer']} (MRA {float(B[i]['score']):.1f}); trace: {short(b16['raw_generation'])}")
    L.append(f"- R1 m100: answer {D['R1m100'][s][i]['extracted_answer']} at B2048 (MRA {x['score']:.1f}; forced close {x['forced']}; 16k cap {bool(r16['hit_token_cap'])}); trace: {short(r16['raw_generation'], 300)}")
    L.append(f"- D0 m100: answer {D['D0m100'][s][i]['extracted_answer']} (MRA {float(D['D0m100'][s][i]['score']):.1f}); trace: {short(d16['raw_generation'], 200)}")
    L.append('')
open('Q2_TRACES.md', 'w').write('\n'.join(L)); print('\n'.join(L))
