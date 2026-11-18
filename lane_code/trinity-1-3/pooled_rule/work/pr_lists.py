"""Write the registered item lists (id, room, type; sorted by id) so that `sha256sum` reproduces the pins of pooled_harm_rule.py."""
import json, hashlib
import pooled_harm_rule as R
out = {}
for d, fn in (('S', 'ITEMS_DEV_S1.tsv'), ('R', 'ITEMS_R0_DEV.tsv')):
    b = R.BASE[d]
    rows = R.load([b['path']], b['family'], tuple(R.N_ITEMS[d]))
    text = ''.join('%s\t%s\t%s\n' % (i, rows[i]['room'], rows[i]['task_type']) for i in sorted(rows))
    open(fn, 'w').write(text)
    h = hashlib.sha256(text.encode()).hexdigest()
    assert h == b['items_sha256'], (fn, h)
    out[fn] = dict(sha256=h, items=len(rows), rooms=len({r['room'] for r in rows.values()}))
out['ROOM_LIST.txt'] = dict(sha256=hashlib.sha256(open('ROOM_LIST.txt', 'rb').read()).hexdigest())
assert out['ROOM_LIST.txt']['sha256'] == R.ROOM_LIST_SHA256
out['pooled_harm_rule.py'] = dict(sha256=hashlib.sha256(open('pooled_harm_rule.py', 'rb').read()).hexdigest())
out['weights_dev_s1'] = {t: '%d/%d = %.4f' % (R.N_ITEMS['S'][t], R.N_ITEMS['S'][t] + R.N_ITEMS['R'][t], R.N_ITEMS['S'][t] / (R.N_ITEMS['S'][t] + R.N_ITEMS['R'][t])) for t in R.SHARED}
json.dump(out, open('REGISTERED_PINS.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
