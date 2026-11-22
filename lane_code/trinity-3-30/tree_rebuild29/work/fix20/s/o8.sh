export TZ=UTC; date -u +%TZ
python3 -I - <<'EOF'
import json, hashlib
O='/project/community/jjyeung/okh7/x_22c714e1/o/174246'
def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def dig(v): return hashlib.sha256(enc(v).encode()).hexdigest()
A='b05f17046ad109b0ee2f6c810b47c9e3bc100e4676e35c40a7ac02cdc449d019'
B='c82d9bc390be047c752f8925b44f0bc5d2ba325405986860ddea077e732465ed'
C='8baae679a7dcce952863e2cf12a3265bf15729ccb5dfa9efd9011e49ce4a0bb0'
d=json.load(open(O+'/refresh.json'))
for k in ('current','source'):
    v=d[k]; vals=set(v.values())
    print(k, 'entries', len(v), 'digest', dig(v), 'A', A in vals, 'B', B in vals, 'C', C in vals)
cur, src = d['current'], d['source']
print('names only in current', len(set(cur)-set(src)), 'only in source', len(set(src)-set(cur)), 'same name other hash', sum(1 for k in cur if k in src and cur[k]!=src[k]))
print('removals_regenerated', json.dumps(d.get('removals_regenerated'))[:300])
print('config', json.dumps(d.get('config'))[:200])
EOF
