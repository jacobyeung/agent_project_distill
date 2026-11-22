export TZ=UTC; date -u +%TZ
python3 -I - <<'EOF'
import json, hashlib
X='/project/community/jjyeung/okh7/x_22c714e1'
O=X+'/o/174246'
def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def dig(v): return hashlib.sha256(enc(v).encode()).hexdigest()
A='b05f17046ad109b0ee2f6c810b47c9e3bc100e4676e35c40a7ac02cdc449d019'
B='c82d9bc390be047c752f8925b44f0bc5d2ba325405986860ddea077e732465ed'
C='8baae679a7dcce952863e2cf12a3265bf15729ccb5dfa9efd9011e49ce4a0bb0'
def find(d, key, path='', out=None, depth=0):
    out=[] if out is None else out
    if isinstance(d, dict) and depth<8:
        for k,v in d.items():
            if k==key: out.append((path+'/'+k, v))
            find(v, key, path+'/'+k, out, depth+1)
    elif isinstance(d, list) and depth<8:
        for i,v in enumerate(d[:50]): find(v, key, path+'/'+str(i), out, depth+1)
    return out
for n in ('refresh.json','a3r.json'):
    try:
        raw=open(O+'/'+n).read(); d=json.loads(raw)
        print('==', n, len(raw), 'status', json.dumps(d.get('status'))[:80], 'same_selection', json.dumps(d.get('same_selection'))[:120])
        for k in ('config','current','source'):
            v=d.get(k); s=json.dumps(v)
            print('   ', k, type(v).__name__, len(s), (sorted(v)[:24] if isinstance(v, dict) else s[:200]))
        hits=find(d,'implementation')
        print('    implementation fields found', len(hits))
        for p,v in hits[:4]:
            if isinstance(v, dict):
                vals=set(v.values())
                print('      ', p, 'entries', len(v), 'digest', dig(v), 'A', A in vals, 'B', B in vals, 'C', C in vals)
            else:
                print('      ', p, type(v).__name__, json.dumps(v)[:120])
        print('    raw counts: A', raw.count(A), 'B', raw.count(B), 'C', raw.count(C), '74640a29', raw.count('74640a29f939ce2a'), '0dd39e28', raw.count('0dd39e28e4c438ba'))
    except Exception as e:
        print('==', n, 'ERR', type(e).__name__, str(e)[:100])
try:
    d=json.load(open(X+'/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73'))
    ip=d.get('inputs_pinned') or {}
    print('== pin inputs_pinned keys', sorted(ip), 'config_sha256', ip.get('config_sha256'))
    print('   s1_routing keys', sorted(ip.get('s1_routing') or {}), 'selection', json.dumps((ip.get('s1_routing') or {}).get('selection'))[:220])
except Exception as e:
    print('== pin ERR', type(e).__name__, str(e)[:100])
for n in ('q.steps','live/174246.steps'):
    try:
        lines=[l.rstrip('\n') for l in open(O+'/'+n)]
        print('==', n, len(lines));
        for l in lines[-6:]: print('   ', l[:160])
        break
    except Exception as e:
        print('==', n, 'ERR', type(e).__name__)
EOF
