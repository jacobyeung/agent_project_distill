export TZ=UTC; date -u +%TZ
python3 -I - <<'EOF'
import json, hashlib, os
X='/project/community/jjyeung/okh7/x_22c714e1'
O=X+'/o/174246'
def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def dig(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def fsha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
needles={'seal':'9d2bbb8ad209d91e','tar':'5f2d77c4bc9905d8','job_config':'f6250f700cf56d2e','kit_c':'76de3706b8eba5b8','kit_n':'4b8b9533eb124341','code_pin':'b2ba52d6b630a492'}
docs={}
for n in ('receipt.json','materialization.json','refresh.json'):
    p=O+'/'+n
    try:
        raw=open(p).read(); d=json.loads(raw); docs[n]=d
        print('==', n, len(raw), 'file sha', fsha(p)[:12], 'digest', dig(d)[:12], 'schema', d.get('schema'))
        print('   needles', {k:raw.count(v) for k,v in needles.items()})
        print('   keys', sorted(d)[:40])
    except Exception as e:
        print('==', n, 'ERR', type(e).__name__, str(e)[:100])
r=docs.get('receipt.json') or {}; m=docs.get('materialization.json') or {}; f=docs.get('refresh.json') or {}
print('== receipt pins: source', json.dumps(r.get('source'))[:200], '| materialization', json.dumps(r.get('materialization'))[:200], '| database', json.dumps(r.get('database'))[:200])
print('== materialization: resolved_selection', json.dumps(m.get('resolved_selection'))[:200], '| relocation', json.dumps(m.get('relocation'))[:200], '| inputs.selection', json.dumps((m.get('inputs') or {}).get('selection'))[:200])
impl=f.get('implementation')
if isinstance(impl, dict):
    vals=set(impl.values())
    print('== refresh implementation entries', len(impl), 'digest', dig(impl), 'file A present', 'b05f17046ad109b0ee2f6c810b47c9e3bc100e4676e35c40a7ac02cdc449d019' in vals, 'file B present', 'c82d9bc390be047c752f8925b44f0bc5d2ba325405986860ddea077e732465ed' in vals, 'file C present', '8baae679a7dcce952863e2cf12a3265bf15729ccb5dfa9efd9011e49ce4a0bb0' in vals)
else:
    print('== refresh implementation', type(impl).__name__)
sel=[v for v in (r.get('source'), m.get('resolved_selection'), (m.get('inputs') or {}).get('selection')) if isinstance(v, dict)]
for v in sel:
    s=v.get('sha256','')
    print('   pin', s[:12], v.get('path','')[-60:], 'count in receipt', enc(r).count(s), 'in materialization', enc(m).count(s), 'equals refresh file sha', s==fsha(O+'/refresh.json'))
for v in sel:
    p=v.get('path','')
    if os.path.isfile(p):
        try:
            d=json.load(open(p)); i=d.get('implementation')
            print('   pinned file', p[-50:], 'schema', d.get('schema'), 'implementation entries', len(i) if isinstance(i, dict) else None, 'digest', dig(i)[:16] if isinstance(i, dict) else None)
        except Exception as e:
            print('   pinned file ERR', type(e).__name__, str(e)[:80])
    else:
        print('   pinned path not on this host:', p[-60:])
p=X+'/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73'
try:
    raw=open(p).read(); d=json.loads(raw)
    print('== kit routing selection pin', len(raw), 'keys', sorted(d)[:30])
    print('   regenerated_sha256', d.get('regenerated_sha256'), 'needles', {k:raw.count(v) for k,v in needles.items()})
    for k,v in d.items():
        s=json.dumps(v)
        if len(s)<260: print('   ', k, s)
        else: print('   ', k, '<', len(s), 'chars>', s[:200])
except Exception as e:
    print('== kit routing selection pin ERR', type(e).__name__, str(e)[:100])
EOF
