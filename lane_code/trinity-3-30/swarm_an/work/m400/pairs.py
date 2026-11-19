import json,re; from collections import Counter, defaultdict
D=json.load(open('/tmp/san_dircls.json'))
def key(i): return re.sub(r'^(forwardtwin|backdir)_','',i)
def rp(x):
    """pre-turn (forward) relation as stated, normalised to the label space of the forward twin"""
    fb,lr=x['fb'],x['lr']
    if x['type']=='hard': return (fb or '?')+'-'+(lr or '?')
    if x['type']=='medium':
        if fb=='back': return 'back'
        return lr
    return lr
ang={}
for x in D['S1|544|forward']:
    m=re.search(r'(\d+) degrees (left|right|from)',x['relline'] or '')
    ang[key(x['id'])]=int(m.group(1)) if m else None
print('ids',D['R1|400|forward'][0]['id'],D['R1|400|away'][0]['id'])
for st in ('544','200','400'):
    run='S1' if st=='544' else 'R1'
    F={key(x['id']):x for x in D['%s|%s|forward'%(run,st)]}; A={key(x['id']):x for x in D['%s|%s|away'%(run,st)]}
    ks=[k for k in F if k in A]
    print('== step',st,'pairs',len(ks))
    for ty in ('easy','medium','hard'):
        c=Counter()
        for k in ks:
            f,a=F[k],A[k]
            if f['type']!=ty: continue
            same = rp(f)==rp(a) if st!='544' else None
            fwd_ok = rp(f)==f['truth'] if ty!='medium' else (rp(f)==f['truth'])
            c[('F right' if f['right'] else 'F wrong', 'A right' if a['right'] else 'A wrong', 'prerel same' if same else 'prerel differs')]+=1
        print(' ',ty,dict(c))
    # toward hard wrong: detail
    for k in ks:
        f,a=F[k],A[k]
        if f['type']=='hard' and not f['right']:
            print('   %s truth %s | F says %s | A pre-turn %s -> A final %s (A truth %s, %s) | 544 angle %s'%(k[-6:],f['truth'],f['final'],rp(a),a['final'],a['truth'],'R' if a['right'] else 'W',ang.get(k)))
# 544 angle of toward-hard items: wrong at 400 vs right at 400
F4={key(x['id']):x for x in D['R1|400|forward']}
for ty in ('hard',):
    for lab in (True,False):
        v=[ang[k] for k,x in F4.items() if x['type']==ty and x['right']==lab and ang.get(k) is not None and str(x['truth']).startswith('back')]
        print('toward hard, truth back, right at 400 =',lab,'544 angles',sorted(v))
