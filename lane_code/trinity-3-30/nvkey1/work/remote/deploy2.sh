set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; mkdir -p $K/kit $K/queue $K/ctl $K/out $K/scores
cat > $K/kit/nvrun.py <<'PYEOF'
#!/usr/bin/env python3
"""nvkey1 NV runner. One process sends every NV request of lane nvkey1 (trinity-2-28).
Jobs: K/queue/<prio>_<job>.jsonl, one task per line:
  {"id": str, "model": "<route id>", "effort": "high"|"medium"|null, "max_tokens": int,
   "content": [{"text": str} | {"image": "/abs/frame.png", "max_side": 640, "mark": [u, v] (0-1000 grid, optional)}],
   "meta": {...}}
Results: K/out/<job>.jsonl, one line per finished task (id, model, served, text, usage, dollars, ...). Finished ids are skipped on restart.
Control files in K/ctl: RATE (requests per minute, 5-minute mean, default 4), INFLIGHT (default 8), BPS (upload bytes/s, default 1.5e6),
BUDGET (dollars at list price over all jobs this runner ever ran, default 600), STOP. Every call is logged in K/meter/CALLS.jsonl.
Stops before the next call: K/ctl/STOP, B/events/nvkey/STOP, an ALLOC.md line 'STOP nvkey1', any BLOCK line or Think3D r3243-r3245 line in
ALLOC.md written after the runner started, the budget reached, or a WAF 429 (then it appends BLOCK to ALLOC.md and exits).
A 429 without WAF header or a 503 backs off and halves RATE and INFLIGHT. A reply whose served model differs from the request is a fault.
Keys come from the environment (NV_INFERENCE_API_KEY, _KEY2.._KEY4) or the export lines of ~/.bashrc; they are never printed or written."""
import base64, glob, io, json, os, re, sys, threading, time, traceback, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
EV = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/nvkey'
ALLOC = '/data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md'
URL = 'https://inference-api.nvidia.com/v1/chat/completions'
PRICE = {  # dollars per token, in / out (NV catalogue cost table, 2026-11-20)
    'gcp/google/gemini-4-argon': (2e-6, 1e-5), 'gcp/google/gemini-3.1-pro-preview': (2e-6, 1.2e-5), 'gcp/google/gemini-3.8-flash': (7.5e-7, 3.75e-6),
    'azure/anthropic/claude-opus-5-5': (4e-6, 2e-5), 'aws/anthropic/bedrock-claude-opus-5-5': (4e-6, 2e-5), 'azure/anthropic/claude-sonnet-5-5': (2e-6, 1e-5),
    'openai/openai/gpt-6.2-astra': (8e-6, 4e-5), 'azure/openai/gpt-6-astra': (1e-5, 5e-5), 'azure/openai/gpt-6.1-terra': (1e-6, 5e-6),
    'xai/xai/grok-4.7': (2e-6, 6e-6), 'nvidia/moonshotai/kimi-k3.1-pro': (1.6e-6, 8e-6)}
PREFIX = ('gcp/google/', 'vertex_ai/', 'gemini/', 'google/', 'models/', 'openai/openai/', 'azure/openai/', 'us/azure/openai/', 'azure/anthropic/',
          'aws/anthropic/bedrock-', 'aws/anthropic/', 'anthropic/', 'bedrock/', 'azure/', 'openai/', 'xai/xai/', 'xai/', 'nvidia/moonshotai/', 'moonshotai/')

def logical(m):
    m = str(m or '').lower()
    for _ in range(3):
        for p in PREFIX:
            if m.startswith(p): m = m[len(p):]
    return m.replace('.', '-')

def same_model(req, served):
    a, b = logical(req), logical(served)
    return b == a or b.startswith(a + '-2') or b.startswith(a + '@') or b.startswith(a + '-v') or b.startswith(a + '-preview')

def load_keys():
    names = ['NV_INFERENCE_API_KEY', 'NV_INFERENCE_API_KEY2', 'NV_INFERENCE_API_KEY3', 'NV_INFERENCE_API_KEY4']
    vals = {n: os.environ.get(n) for n in names}
    if not all(vals.values()):
        try:
            for line in open(os.path.expanduser('~/.bashrc')):
                m = re.match(r'\s*export\s+(NV_INFERENCE_API_KEY\d?)=(.*)$', line)
                if m and not vals.get(m.group(1)):
                    vals[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        except OSError: pass
    keys = [vals[n] for n in names if vals.get(n)]
    assert keys, 'no NV key found'
    return keys

def rint(name, default, cast=float):
    try: return cast(open(os.path.join(K, 'ctl', name)).read().strip())
    except Exception: return default

def utc(t=None): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t if t is not None else time.time()))

def encode_image(path, max_side=640, mark=None, quality=90):
    im = Image.open(path).convert('RGB'); w, h = im.size; s = min(1.0, float(max_side) / max(w, h))
    if s < 1.0: im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    if mark is not None:
        W, H = im.size; x, y = mark[0] / 1000.0 * W, mark[1] / 1000.0 * H; d = ImageDraw.Draw(im); r = max(6, round(0.018 * max(W, H)))
        for rr, col in ((r + 2, (0, 0, 0)), (r, (255, 0, 0)), (r - 2, (0, 0, 0))):
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col, width=2)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=quality)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode(), im.size

class Runner:
    def __init__(self):
        for d in ('queue', 'out', 'meter', 'ctl', 'faults'): os.makedirs(os.path.join(K, d), exist_ok=True)
        self.keys = load_keys(); self.kidx = 0; self.lock = threading.Lock(); self.starts = []; self.inflight = 0
        self.t0 = time.time(); self.bytes_tokens = 0.0; self.bytes_t = time.time(); self.stop_reason = None
        self.spent = 0.0; self.calls = 0; self.backoff_until = 0.0; self.alloc_seen = self._alloc_len(); self.last_check = 0.0
        self.spent = self._meter_spend(); self.mlock = threading.Lock(); self.model_faults = {}; self.bad_models = set()
        self.meter = open(os.path.join(K, 'meter', 'CALLS.jsonl'), 'a')
        self.log('start spent %.4f keys %d' % (self.spent, len(self.keys)))

    def mwrite(self, rec):
        with self.mlock:
            self.meter.write(json.dumps(rec) + '\n'); self.meter.flush()

    def _meter_spend(self):
        s = 0.0
        try:
            for l in open(os.path.join(K, 'meter', 'CALLS.jsonl')):
                try: s += json.loads(l).get('dollars', 0.0) or 0.0
                except Exception: pass
        except OSError: pass
        return s

    def _alloc_len(self):
        try: return len(open(ALLOC).read().splitlines())
        except OSError: return 0

    def log(self, msg):
        with open(os.path.join(K, 'runner.log'), 'a') as f: f.write('%s %s\n' % (utc(), msg))

    def check_stops(self):
        now = time.time()
        if now - self.last_check < 15: return self.stop_reason
        self.last_check = now
        if os.path.exists(os.path.join(K, 'ctl', 'STOP')): self.stop_reason = 'local STOP'
        try:
            if os.path.exists(os.path.join(EV, 'STOP')): self.stop_reason = 'events STOP'
            lines = open(ALLOC).read().splitlines()
            for l in lines:
                if 'STOP nvkey1' in l and 'stops me' not in l: self.stop_reason = 'ALLOC STOP nvkey1'
            for l in lines[self.alloc_seen:]:
                if ' BLOCK' in l and 'nvkey1' not in l: self.stop_reason = 'ALLOC BLOCK: ' + l[:120]
                if re.search(r'r324[345]|think3d', l, re.I) and re.search(r'HOLD|START|LAUNCH|GATE', l): self.stop_reason = 'ALLOC Think3D: ' + l[:120]
        except OSError: pass
        if self.spent >= rint('BUDGET', 600.0): self.stop_reason = 'budget %.2f reached' % self.spent
        return self.stop_reason

    def admit(self, nbytes):
        """Block until rate, in-flight and byte limits admit one request; return False when stopping."""
        while True:
            if self.check_stops(): return False
            with self.lock:
                now = time.time(); rate = rint('RATE', 4.0); cap = rint('INFLIGHT', 8, int); bps = rint('BPS', 1.5e6)
                self.starts = [t for t in self.starts if now - t < 300]
                last60 = sum(1 for t in self.starts if now - t < 60)
                mean5 = len(self.starts) / 5.0
                self.bytes_tokens = min(bps * 8, self.bytes_tokens + (now - self.bytes_t) * bps); self.bytes_t = now
                ok = (now >= self.backoff_until and self.inflight < cap and last60 < max(1, rate) and mean5 < rate + 0.01 and self.bytes_tokens >= min(nbytes, bps * 8) * 0.999)
                if ok:
                    self.starts.append(now); self.inflight += 1; self.bytes_tokens -= nbytes; return True
            time.sleep(1.0)

    def release(self):
        with self.lock: self.inflight -= 1

    def post(self, body, slot):
        data = json.dumps(body).encode()
        req = urllib.request.Request(URL, data=data, method='POST', headers={'Content-Type': 'application/json', 'dataClassification': 'sensitive',
                                     'Authorization': 'Bearer ' + self.keys[slot % len(self.keys)]})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                return r.status, dict(r.headers), r.read(), time.time() - t, len(data)
        except urllib.error.HTTPError as e:
            try: payload = e.read()
            except Exception: payload = b''
            return e.code, dict(e.headers or {}), payload, time.time() - t, len(data)
        except Exception as e:
            return -1, {}, repr(e).encode()[:2000], time.time() - t, len(data)

    def build(self, task):
        content = []; sizes = []
        for c in task['content']:
            if 'text' in c: content.append({'type': 'text', 'text': c['text']})
            else:
                url, sz = encode_image(c['image'], c.get('max_side', 640), c.get('mark'))
                content.append({'type': 'image_url', 'image_url': {'url': url, 'detail': 'high'}}); sizes.append(sz)
        body = {'model': task['model'], 'messages': [{'role': 'user', 'content': content}], 'max_tokens': task.get('max_tokens', 16384)}
        if task.get('effort'): body['reasoning_effort'] = task['effort']
        body.update(task.get('extra') or {})
        return body, sizes

    def run_task(self, job, task, outf, olock):
        if task['model'] in self.bad_models:
            with open(os.path.join(K, 'faults', job + '.gaveup.jsonl'), 'a') as f: f.write(json.dumps({'id': task['id'], 'utc': utc(), 'why': 'model faulted'}) + '\n')
            return
        try: body, sizes = self.build(task)
        except Exception as e:
            self.log('BUILD FAIL %s %s %r' % (job, task['id'], e)); return
        nbytes = len(json.dumps(body))
        for attempt in range(3):
            if not self.admit(nbytes): return
            with self.lock: slot = self.kidx; self.kidx += 1
            try: status, hdr, payload, secs, sent = self.post(body, slot)
            finally: self.release()
            h = {k.lower(): v for k, v in hdr.items()}
            rec = {'utc': utc(), 'job': job, 'id': task['id'], 'model': task['model'], 'attempt': attempt, 'status': status, 'secs': round(secs, 1),
                   'bytes': sent, 'key_slot': slot % len(self.keys), 'images': len(sizes)}
            if status == 429 and any(k.startswith('x-amzn-waf') for k in h):
                rec['waf'] = True; self.mwrite(rec)
                self.waf(rec); return
            if status in (429, 503) or status >= 500 or status == -1:
                rec['err'] = payload[:300].decode(errors='ignore'); self.mwrite(rec)
                if status in (429, 503):
                    with self.lock:
                        self.backoff_until = max(self.backoff_until, time.time() + 60 * (attempt + 1))
                        for name, lo in (('RATE', 1.0), ('INFLIGHT', 1)):
                            v = rint(name, 4.0 if name == 'RATE' else 8); nv = max(lo, v / 2.0)
                            open(os.path.join(K, 'ctl', name), 'w').write('%s\n' % (int(nv) if name == 'INFLIGHT' else round(nv, 2)))
                    self.log('BACKOFF %s status %s: RATE and INFLIGHT halved' % (task['id'], status))
                else: time.sleep(20 * (attempt + 1))
                continue
            try: resp = json.loads(payload)
            except Exception:
                rec['err'] = 'unparsable %d bytes' % len(payload); self.mwrite(rec); continue
            if status != 200:
                rec['err'] = json.dumps(resp)[:400]; self.mwrite(rec)
                if status in (400, 401, 403, 404, 413, 422): break
                continue
            served = resp.get('model'); u = resp.get('usage') or {}
            pin, pout = PRICE.get(task['model'], (None, None))
            ptok = u.get('prompt_tokens') or 0; ctok = u.get('completion_tokens') or 0
            rtok = ((u.get('completion_tokens_details') or {}).get('reasoning_tokens')) or 0
            dollars = (ptok * pin + ctok * pout) if pin is not None else None
            hcost = h.get('x-litellm-response-cost'); rec['fallbacks'] = h.get('x-litellm-attempted-fallbacks'); rec['litellm_model_id'] = h.get('x-litellm-model-id')
            rec.update(served=served, prompt_tokens=ptok, completion_tokens=ctok, reasoning_tokens=rtok, dollars=dollars, header_cost=hcost,
                       finish=((resp.get('choices') or [{}])[0]).get('finish_reason'))
            if dollars is None and hcost:
                try: rec['dollars'] = dollars = float(hcost)
                except ValueError: pass
            with self.lock: self.spent += dollars or 0.0; self.calls += 1
            fault = None if same_model(task['model'], served) else 'served model %r for %r' % (served, task['model'])
            if dollars is None: fault = (fault or '') + ' no price'
            rec['fault'] = fault
            self.mwrite(rec)
            if fault:
                with open(os.path.join(K, 'faults', job + '.jsonl'), 'a') as f: f.write(json.dumps(rec) + '\n')
                if dollars is None: self.stop_reason = 'spend cannot be counted (%s)' % task['model']; return
                with self.lock:
                    self.model_faults[task['model']] = self.model_faults.get(task['model'], 0) + 1
                    if self.model_faults[task['model']] >= 3: self.bad_models.add(task['model'])
                if task['model'] in self.bad_models: self.log('MODEL FAULTED %s (served %r): its tasks are skipped' % (task['model'], served)); break
                if attempt >= 1: break
                continue
            msg = ((resp.get('choices') or [{}])[0]).get('message') or {}
            out = {'id': task['id'], 'job': job, 'model': task['model'], 'served': served, 'utc': utc(), 'text': msg.get('content'),
                   'finish': rec['finish'], 'usage': {'prompt': ptok, 'completion': ctok, 'reasoning': rtok}, 'dollars': dollars,
                   'header_cost': hcost, 'secs': rec['secs'], 'sizes': sizes, 'meta': task.get('meta', {})}
            with olock:
                outf.write(json.dumps(out) + '\n'); outf.flush()
            return
        self.log('GAVE UP %s %s' % (job, task['id']))
        with open(os.path.join(K, 'faults', job + '.gaveup.jsonl'), 'a') as f: f.write(json.dumps({'id': task['id'], 'utc': utc()}) + '\n')

    def waf(self, rec):
        self.stop_reason = 'WAF 429'
        with self.lock:
            rate5 = len([t for t in self.starts if time.time() - t < 300]) / 5.0
        try:
            with open(ALLOC, 'a') as f:
                f.write('%sZ BLOCK distill nvkey1: WAF 429 (x-amzn-waf-rule) on this lane at %.1f requests/min (5-min mean, this lane only); all nvkey1 traffic stopped; no probe; it restarts only on the orchestrator\'s word\n' % (utc()[:16], rate5))
        except OSError: pass
        try:
            T = time.strftime('%Y%m%dT%H%MZ', time.gmtime())
            open(os.path.join(EV, T + '_BLOCKER_nvkey1_waf429.md'), 'w').write('# nvkey1 BLOCKER: WAF 429 from the NV front door\nAt %s a request of job %s got HTTP 429 with an x-amzn-waf-rule header at %.1f requests/min from this lane. All nvkey1 traffic stopped and BLOCK was appended to nv_slots/ALLOC.md. No probe was sent. Restart needs an ORCH answer.\n' % (rec['utc'], rec['job'], rate5))
        except OSError: pass
        self.log('WAF 429 -> stopped')

    def write_meter(self):
        now = time.time()
        with self.lock: r5 = len([t for t in self.starts if now - t < 300]) / 5.0; infl = self.inflight
        m = {'utc': utc(), 'lane': 'nvkey1', 'host': os.uname()[1], 'req_min5': round(r5, 2), 'inflight': infl, 'rate_target': rint('RATE', 4.0),
             'dollars_list_total': round(self.spent, 4), 'calls_this_run': self.calls, 'stop_reason': self.stop_reason}
        try:
            tmp = os.path.join(EV, '.METER.json.tmp'); open(tmp, 'w').write(json.dumps(m) + '\n'); os.replace(tmp, os.path.join(EV, 'METER.json'))
        except OSError: pass
        open(os.path.join(K, 'meter', 'METER.json'), 'w').write(json.dumps(m) + '\n')

    def jobs(self):
        return sorted(glob.glob(os.path.join(K, 'queue', '*.jsonl')))

    def main(self, idle_exit=1800):
        ex = ThreadPoolExecutor(max_workers=16); pending = {}; idle_since = time.time(); last_meter = 0
        while True:
            if time.time() - last_meter > 60: self.write_meter(); last_meter = time.time()
            if self.check_stops():
                self.log('STOP: %s' % self.stop_reason); break
            submitted = False
            for qf in self.jobs():
                job = os.path.basename(qf)[:-6]
                if job in pending and pending[job]: continue
                op = os.path.join(K, 'out', job + '.jsonl')
                done = set()
                for fp in (op, os.path.join(K, 'faults', job + '.gaveup.jsonl')):
                    if os.path.exists(fp):
                        for l in open(fp):
                            try: done.add(json.loads(l)['id'])
                            except Exception: pass
                tasks = [json.loads(l) for l in open(qf) if l.strip()]
                todo = [t for t in tasks if t['id'] not in done]
                if not todo: continue
                outf = open(op, 'a'); olock = threading.Lock()
                pending[job] = [ex.submit(self.run_task, job, t, outf, olock) for t in todo]
                self.log('JOB %s: %d of %d tasks submitted' % (job, len(todo), len(tasks))); submitted = True
                break
            live = {j: [f for f in fs if not f.done()] for j, fs in pending.items()}
            pending = {j: fs for j, fs in live.items() if fs}
            if pending or submitted: idle_since = time.time()
            elif time.time() - idle_since > idle_exit: self.log('idle exit'); break
            time.sleep(5)
        self.write_meter()
        ex.shutdown(wait=True, cancel_futures=True); self.write_meter(); self.log('exit spent %.4f' % self.spent)

if __name__ == '__main__':
    Runner().main(int(sys.argv[1]) if len(sys.argv) > 1 else 1800)
PYEOF
cat > $K/kit/c1_jobs.py <<'PYEOF'
"""nvkey1: build fat presence-and-point labelling tasks for K1 calibration captures (one call = every class of a capture x all frames).
usage: c1_jobs.py OUT.jsonl MODEL EFFORT NFRAMES(32|64) [alias,alias,...|all] [max_side]
Frames: /scratch/jjyeung/k1_frames/<sha[:2]>/<sha>.png; truth stays in work/c1 and is never sent."""
import json, os, sys
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
FR = '/scratch/jjyeung/k1_frames'
PROMPT = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
          'Object kinds: {kinds}.\n'
          'For every frame and every object kind, decide whether at least one object of that kind is visible in that frame, fully or partly '
          '(partly visible or partly occluded objects count; reflections and pictures of objects do not). '
          'If it is visible, give one point on a visible part of it (if several are visible, pick the most visible one) as [x, y] in 0-1000 coordinates '
          'of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. If it is not visible, give null.\n'
          'Reply with one JSON object and nothing else, with one entry for every frame from 1 to {n} and every object kind: '
          '{{"1": {{"{k0}": [x, y] or null, ...}}, "2": {{...}}, ..., "{n}": {{...}}}}')
def main():
    out, model, effort, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    extra = json.loads(os.environ.get('C1_EXTRA', '{}')); effort = None if effort == 'none' else effort
    sel = sys.argv[5] if len(sys.argv) > 5 else 'all'; side = int(sys.argv[6]) if len(sys.argv) > 6 else 640
    man = json.load(open(K + '/c1/C1_MANIFEST.json'))
    aliases = list(man) if sel == 'all' else sel.split(',')
    tag = model.split('/')[-1]
    with open(out, 'a') as f:
        for a in aliases:
            m = man[a]; shas = m['anchors'] if n == 32 else m['dense']
            assert len(shas) == n, (a, len(shas))
            kinds = m['classes']
            content = [{'text': PROMPT.format(n=n, kinds=json.dumps(kinds), k0=kinds[0])}]
            for i, s in enumerate(shas):
                p = '%s/%s/%s.png' % (FR, s[:2], s); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
            f.write(json.dumps({'id': '%s_%s_f%d_s%d' % (a, tag, n, side), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'alias': a, 'n': n, 'side': side, 'kinds': kinds, 'slots': m['anchor_slots'] if n == 64 else list(range(32))}}) + '\n')
    print('wrote', len(aliases), 'tasks to', out)
main()
PYEOF
cat > $K/kit/score_c1.py <<'PYEOF'
"""nvkey1: score fat presence-and-point labels against K1 raster truth at the 32 anchors.
usage: score_c1.py OUT.jsonl [more.jsonl ...] -> prints a table per (model, nframes, side) and writes work/scores/C1_<tag>.json
Truth: visible = class share >= 0.2% in a valid frame; absent = 0 pixels; slivers and invalid frames are not scored.
Point: inside the class mask at raster resolution (exact pixel, and with a 1-pixel tolerance). Intervals: capture-clustered bootstrap, 2,000 draws."""
import json, re, sys, os, collections, random
import numpy as np
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
man = json.load(open(K + '/c1/C1_MANIFEST.json'))
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def band(s):
    return 'absent' if s == 0 else ('<0.2%' if s < 0.002 else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%')))
truth = {}
for a in man:
    z = np.load(K + '/c1/%s.npz' % a, allow_pickle=True); H, W = [int(x) for x in z['shape']]
    mask = np.unpackbits(z['mask'], axis=-1)[..., :W].astype(bool)
    truth[a] = dict(classes=[str(c) for c in z['classes']], share=z['share'], mask=mask, missing=z['missing'], H=H, W=W)
rows = []
for fn in sys.argv[1:]:
    for l in open(fn):
        r = json.loads(l); m = r['meta']; a = m['alias']; T = truth[a]; d = parse(r['text'])
        key = (r['model'].split('/')[-1], m['n'], m.get('side', 640))
        for ci, c in enumerate(T['classes']):
            for k in range(32):
                if T['missing'][k]: continue
                s = float(T['share'][ci, k]); b = band(s)
                if b == '<0.2%': continue
                lab = str(m['slots'][k] + 1) if m['n'] == 64 else str(k + 1)
                v = None if d is None else (d.get(lab) or {}).get(c, 'MISSING') if isinstance(d.get(lab), dict) else 'MISSING'
                if v == 'MISSING' or d is None: said = None
                else: said = v is not None and isinstance(v, (list, tuple)) and len(v) == 2
                hit = hit1 = None
                if said and b != 'absent':
                    x = min(T['W'] - 1, max(0, int(float(v[0]) / 1000.0 * T['W']))); y = min(T['H'] - 1, max(0, int(float(v[1]) / 1000.0 * T['H'])))
                    mk = T['mask'][ci, k]; hit = bool(mk[y, x]); hit1 = bool(mk[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any())
                rows.append(dict(key=key, alias=a, cls=c, k=k, pos=(m['slots'][k] if m['n'] == 64 else k) / float(m['n']), ci=ci, nk=len(T['classes']),
                                 band=b, truth=b != 'absent', said=said, hit=hit, hit1=hit1, parsed=d is not None, ds=man[a]['dataset']))
def boot(sub, f, n=2000):
    caps = sorted(set(r['alias'] for r in sub)); by = collections.defaultdict(list)
    for r in sub: by[r['alias']].append(r)
    rng = random.Random(7); vals = []
    for _ in range(n):
        s = [r for c in (rng.choice(caps) for _ in caps) for r in by[c]]
        v = f(s)
        if v is not None: vals.append(v)
    vals.sort(); return (round(vals[int(0.025 * len(vals))], 1), round(vals[int(0.975 * len(vals)) - 1], 1)) if vals else None
def acc(s):
    s = [r for r in s if r['said'] is not None]; return 100.0 * sum(r['said'] == r['truth'] for r in s) / len(s) if s else None
def ptin(s, f='hit'):
    s = [r for r in s if r['truth'] and r['said']]; return 100.0 * sum(bool(r[f]) for r in s) / len(s) if s else None
res = collections.OrderedDict()
for key in sorted(set(r['key'] for r in rows)):
    R = [r for r in rows if r['key'] == key]; out = collections.OrderedDict()
    out['captures'] = len(set(r['alias'] for r in R)); out['facts'] = len(R); out['unparsed_facts'] = sum(1 for r in R if r['said'] is None)
    out['presence_all'] = (acc(R), boot(R, acc))
    for b in ('>=5%', '1-5%', '0.2-1%', 'absent'):
        S = [r for r in R if r['band'] == b]; out['presence_' + b] = (acc(S), boot(S, acc), len(S))
    S = [r for r in R if r['band'] in ('>=5%', '1-5%')]; out['presence_>=1%'] = (acc(S), boot(S, acc), len(S))
    for b in ('>=5%', '1-5%', '0.2-1%'):
        S = [r for r in R if r['band'] == b]; out['point_' + b] = (ptin(S), boot(S, ptin), sum(1 for r in S if r['said']))
    S = [r for r in R if r['band'] in ('>=5%', '1-5%')]; out['point_>=1%'] = (ptin(S), boot(S, ptin), sum(1 for r in S if r['said'])); out['point_>=1%_tol1'] = (ptin(S, 'hit1'),)
    for q in range(4):
        S = [r for r in R if int(r['pos'] * 4) == q]; out['presence_pos_q%d' % (q + 1)] = acc(S)
    S1 = [r for r in R if r['ci'] < r['nk'] / 2.0]; S2 = [r for r in R if r['ci'] >= r['nk'] / 2.0]; out['presence_first_half_kinds'] = acc(S1); out['presence_second_half_kinds'] = acc(S2)
    for ds in ('arkitscenes', 'scannet', 'scannetpp'):
        S = [r for r in R if r['ds'] == ds]; out['presence_' + ds] = acc(S)
    res['%s|f%d|s%d' % key] = out
    print('%s f%d s%d' % key, json.dumps(out))
os.makedirs(K + '/scores', exist_ok=True)
tag = os.path.basename(sys.argv[1]).replace('.jsonl', '')
json.dump(res, open(K + '/scores/C1_%s.json' % tag, 'w'), indent=1)
PYEOF
cd $K; P=/scratch/jjyeung/envs/p1cpu/bin/python
BO=ka9594e8caae,kc2430767aa3,kc88e2007abb,k01d89b248dc,kf54aa2cf5b1,k03c5a6666c8,kc57e8edfa5c,k234381f08ec
Q=$K/queue/10_bake32.jsonl
if [ ! -f $Q ]; then
  $P -B kit/c1_jobs.py $Q.tmp gcp/google/gemini-4-argon high 32 $BO
  C1_EXTRA='{"thinking": {"type": "enabled", "budget_tokens": 8000}}' $P -B kit/c1_jobs.py $Q.tmp azure/anthropic/claude-opus-5-5 none 32 $BO
  $P -B kit/c1_jobs.py $Q.tmp openai/openai/gpt-6.2-astra high 32 $BO
  $P -B kit/c1_jobs.py $Q.tmp azure/openai/gpt-6.1-terra high 32 $BO
  $P -B kit/c1_jobs.py $Q.tmp gcp/google/gemini-3.8-flash high 32 $BO
  mv $Q.tmp $Q
fi
wc -l $Q; ls -la $Q
echo 4 > $K/ctl/RATE; echo 8 > $K/ctl/INFLIGHT; echo 60 > $K/ctl/BUDGET
tmux kill-session -t nvk1_run 2>/dev/null; sleep 2
CA=/etc/pki/tls/certs/ca-bundle.crt
tmux new-session -d -s nvk1_run "cd $K && SSL_CERT_FILE=$CA NVK=$K $P -B kit/nvrun.py 3600 </dev/null >>$K/runner.stdout 2>&1" </dev/null >/dev/null 2>&1
sleep 20; tmux ls 2>&1 | grep nvk1; tail -4 $K/runner.log
