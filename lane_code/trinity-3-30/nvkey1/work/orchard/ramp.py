"""nvkey1 second-source ramp on an Orchard login node: tiny text requests at 4, 8, 16, 32 per minute in 10-minute steps.
Key from env NVK_A..NVK_D only. Log /tmp/nvk1/ramp.jsonl. Stops at /tmp/nvk1/STOP, at any 429 or 503, or at the end."""
import json, os, sys, time, threading, urllib.request, urllib.error
D = '/tmp/nvk1'; os.makedirs(D, exist_ok=True)
KEYS = [os.environ[k] for k in ('NVK_A', 'NVK_B', 'NVK_C', 'NVK_D') if os.environ.get(k)]
for k in ('NVK_A', 'NVK_B', 'NVK_C', 'NVK_D'): os.environ.pop(k, None)
SCHED = [(4, 10), (8, 10), (16, 10), (32, 10)]
if len(sys.argv) > 1: SCHED = json.loads(sys.argv[1])
URL = 'https://inference-api.nvidia.com/v1/chat/completions'
BODY = json.dumps({'model': 'gcp/google/gemini-3.8-flash', 'messages': [{'role': 'user', 'content': 'Reply with the single word OK.'}], 'max_tokens': 16, 'reasoning_effort': 'low'}).encode()
log = open(D + '/ramp.jsonl', 'a'); lock = threading.Lock(); stop = {'why': None}; n = {'i': 0}
def utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def one(rate):
    with lock: i = n['i']; n['i'] += 1
    req = urllib.request.Request(URL, data=BODY, method='POST', headers={'Content-Type': 'application/json', 'dataClassification': 'sensitive', 'Authorization': 'Bearer ' + KEYS[i % len(KEYS)]})
    t = time.time(); rec = {'utc': utc(), 'i': i, 'rate': rate, 'slot': i % len(KEYS)}
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            h = {k.lower(): v for k, v in r.headers.items()}; d = json.loads(r.read())
            rec.update(status=r.status, served=d.get('model'), cost=h.get('x-litellm-response-cost'), waf=any(k.startswith('x-amzn-waf') for k in h))
    except urllib.error.HTTPError as e:
        h = {k.lower(): v for k, v in (e.headers or {}).items()}; rec.update(status=e.code, waf=any(k.startswith('x-amzn-waf') for k in h), err=(e.read() or b'')[:200].decode(errors='ignore'))
    except Exception as e:
        rec.update(status=-1, err=repr(e)[:200])
    rec['secs'] = round(time.time() - t, 2)
    with lock:
        log.write(json.dumps(rec) + '\n'); log.flush()
        if rec['status'] in (429, 503): stop['why'] = 'HTTP %s waf=%s' % (rec['status'], rec.get('waf'))
for rate, minutes in SCHED:
    end = time.time() + 60 * minutes; gap = 60.0 / rate
    with lock: log.write(json.dumps({'utc': utc(), 'step': rate}) + '\n'); log.flush()
    while time.time() < end and not stop['why']:
        if os.path.exists(D + '/STOP'): stop['why'] = 'STOP file'; break
        threading.Thread(target=one, args=(rate,), daemon=True).start(); time.sleep(gap)
    if stop['why']: break
time.sleep(30)
with lock: log.write(json.dumps({'utc': utc(), 'end': stop['why'] or 'schedule done', 'requests': n['i']}) + '\n'); log.flush()
