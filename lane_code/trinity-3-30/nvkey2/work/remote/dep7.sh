K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
cat > $K/kit/nvrun.py.new <<'PYEOF'
#!/usr/bin/env python3
"""nvkey1 NV runner. One process sends every NV request of lane nvkey1 (trinity-2-28).
Jobs: K/queue/<prio>_<job>.jsonl, one task per line:
  {"id": str, "model": "<route id>", "effort": "high"|"medium"|null, "max_tokens": int,
   "content": [{"text": str} | {"image": "/abs/frame.png", "max_side": 640, "mark": [u, v] (0-1000 grid, optional)}],
   "meta": {...}}
Results: K/out/<job>.jsonl, one line per finished task (id, model, served, text, usage, dollars, ...). Finished ids are skipped on restart.
Control files in K/ctl: RATE (requests per minute, 5-minute mean, default 4), INFLIGHT (default 8), BPS (upload bytes/s, default 1.5e6),
BUDGET (dollars at list price over all jobs this runner ever ran, default 600), STOP. Every call is logged in K/meter/CALLS.jsonl.
Stops before the next call: K/ctl/STOP, B/events/nvkey/STOP, an ALLOC.md line 'STOP nvkey1' or 'STOP nvkey2', any line whose second token is BLOCK, or a Think3D r3243-r3245 line in
ALLOC.md written after the runner started, the budget reached, or a WAF 429 (then it appends BLOCK to ALLOC.md and exits).
A 429 without WAF header or a 503 backs off and halves RATE and INFLIGHT. A reply whose served model differs from the request is a fault.
Keys come from the environment (NV_INFERENCE_API_KEY, _KEY2.._KEY4) or the export lines of ~/.bashrc; they are never printed or written.
Tags (nvkey2): every task of a job with work left carries meta.tag in train | calibration | dev-analysis | eval and meta.scenes (canonical names). A train
(label) job whose scenes hit kit/excl.py is refused whole; a calibration job may use V1's calibration captures but nothing else excl.py refuses; dev-analysis results go to K/analysis_only/out/<job>.jsonl; eval jobs
run only while K/ctl/EVAL_OK exists. BUDGET_PROXY (proxy-reported dollars, the working figure) stops the runner like BUDGET (list dollars)."""
import base64, glob, hashlib, io, json, os, re, sys, threading, time, traceback, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
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
    b = io.BytesIO(); im.save(b, 'JPEG', quality=quality); raw = b.getvalue()
    return 'data:image/jpeg;base64,' + base64.b64encode(raw).decode(), im.size, hashlib.sha256(raw).hexdigest(), (w, h)

class Runner:
    def __init__(self):
        for d in ('queue', 'out', 'meter', 'ctl', 'faults', 'analysis_only/out'): os.makedirs(os.path.join(K, d), exist_ok=True)
        self.refused = set(); self.proxy = 0.0
        self.keys = load_keys(); self.kidx = 0; self.lock = threading.Lock(); self.starts = []; self.inflight = 0
        self.t0 = time.time(); self.bytes_tokens = 0.0; self.bytes_t = time.time(); self.stop_reason = None
        self.spent = 0.0; self.calls = 0; self.backoff_until = 0.0; self.alloc_seen = self._alloc_len(); self.last_check = 0.0
        self.spent, self.proxy = self._meter_spend(); self.mlock = threading.Lock(); self.model_faults = {}; self.bad_models = set()
        self.meter = open(os.path.join(K, 'meter', 'CALLS.jsonl'), 'a')
        self.log('start spent list %.4f proxy %.4f keys %d' % (self.spent, self.proxy, len(self.keys)))

    def mwrite(self, rec):
        with self.mlock:
            self.meter.write(json.dumps(rec) + '\n'); self.meter.flush()

    def _meter_spend(self):
        s = p = 0.0
        try:
            for l in open(os.path.join(K, 'meter', 'CALLS.jsonl')):
                try:
                    d = json.loads(l); s += d.get('dollars', 0.0) or 0.0; p += float(d.get('header_cost') or 0.0)
                except Exception: pass
        except OSError: pass
        return s, p

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
                if re.search(r'STOP nvkey[12]\b', l) and 'stops me' not in l: self.stop_reason = 'ALLOC STOP nvkey'
            for l in lines[self.alloc_seen:]:
                tok = l.split()
                if len(tok) > 1 and tok[1].upper().startswith('BLOCK') and not tok[1].upper().startswith('BLOCK-RULING'): self.stop_reason = 'ALLOC BLOCK: ' + l[:120]
                if re.search(r'r324[345]|think3d', l, re.I) and re.search(r'HOLD|START|LAUNCH|GATE', l): self.stop_reason = 'ALLOC Think3D: ' + l[:120]
        except OSError: pass
        if self.spent >= rint('BUDGET', 600.0): self.stop_reason = 'budget %.2f reached' % self.spent
        if self.proxy >= rint('BUDGET_PROXY', 1e9): self.stop_reason = 'proxy budget %.2f reached' % self.proxy
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
        content = []; sizes = []; images = []
        for c in task['content']:
            if 'text' in c: content.append({'type': 'text', 'text': c['text']})
            else:
                url, sz, js, src = encode_image(c['image'], c.get('max_side', 640), c.get('mark'))
                content.append({'type': 'image_url', 'image_url': {'url': url, 'detail': 'high'}}); sizes.append(sz)
                images.append({'src': os.path.basename(c['image']), 'src_wh': list(src), 'wh': list(sz), 'jpeg_sha256': js, 'mark': c.get('mark'),
                               'transform': 'LANCZOS resize to max_side %d, JPEG q90, no crop, no rotation' % c.get('max_side', 640)})
        body = {'model': task['model'], 'messages': [{'role': 'user', 'content': content}], 'max_tokens': task.get('max_tokens', 16384)}
        if task.get('effort'): body['reasoning_effort'] = task['effort']
        body.update(task.get('extra') or {})
        return body, sizes, images

    def run_task(self, job, task, outf, olock):
        if task['model'] in self.bad_models:
            with open(os.path.join(K, 'faults', job + '.gaveup.jsonl'), 'a') as f: f.write(json.dumps({'id': task['id'], 'utc': utc(), 'why': 'model faulted'}) + '\n')
            return
        try: body, sizes, images = self.build(task)
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
            with self.lock:
                self.spent += dollars or 0.0; self.calls += 1
                try: self.proxy += float(hcost or 0.0)
                except ValueError: pass
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
                   'header_cost': hcost, 'secs': rec['secs'], 'sizes': sizes, 'images': images, 'meta': task.get('meta', {})}
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
        m = {'utc': utc(), 'lane': 'nvkey2', 'host': os.uname()[1], 'req_min5': round(r5, 2), 'inflight': infl, 'rate_target': rint('RATE', 4.0),
             'dollars_list_total': round(self.spent, 4), 'dollars_proxy_total': round(self.proxy, 4), 'calls_this_run': self.calls, 'stop_reason': self.stop_reason}
        try:
            tmp = os.path.join(EV, '.METER.json.tmp'); open(tmp, 'w').write(json.dumps(m) + '\n'); os.replace(tmp, os.path.join(EV, 'METER.json'))
        except OSError: pass
        open(os.path.join(K, 'meter', 'METER.json'), 'w').write(json.dumps(m) + '\n')

    def gate(self, job, tasks, tags):
        if len(tags) != 1 or not tags <= {'train', 'calibration', 'dev-analysis', 'eval'}: return 'tags %r: one of train, calibration, dev-analysis, eval per job' % sorted(map(str, tags))
        tag = next(iter(tags))
        if tag == 'eval' and not os.path.exists(os.path.join(K, 'ctl', 'EVAL_OK')): return 'eval job without ctl/EVAL_OK'
        scenes = [s for t in tasks for s in ((t.get('meta') or {}).get('scenes') or [])]
        if tag in ('train', 'calibration'):
            if not all((t.get('meta') or {}).get('scenes') for t in tasks): return '%s task without meta.scenes' % tag
            try: excl.assert_train(sorted(set(scenes)), label=(tag == 'train'))
            except Exception as e: return 'exclusion assert: %s' % str(e)[:300]
        return None

    def jobs(self):
        return sorted(glob.glob(os.path.join(K, 'queue', '*.jsonl')))

    def main(self, idle_exit=1800):
        ex = ThreadPoolExecutor(max_workers=48); pending = {}; idle_since = time.time(); last_meter = 0
        while True:
            if time.time() - last_meter > 60: self.write_meter(); last_meter = time.time()
            if self.check_stops():
                self.log('STOP: %s' % self.stop_reason); break
            submitted = False
            for qf in self.jobs():
                job = os.path.basename(qf)[:-6]
                if job in self.refused or (job in pending and pending[job]): continue
                tasks = [json.loads(l) for l in open(qf) if l.strip()]
                tags = set((t.get('meta') or {}).get('tag') for t in tasks)
                op = os.path.join(K, 'analysis_only/out' if tags == {'dev-analysis'} else 'out', job + '.jsonl')
                done = set()
                for fp in (op, os.path.join(K, 'faults', job + '.gaveup.jsonl')):
                    if os.path.exists(fp):
                        for l in open(fp):
                            try: done.add(json.loads(l)['id'])
                            except Exception: pass
                todo = [t for t in tasks if t['id'] not in done]
                if not todo: continue
                why = self.gate(job, tasks, tags)
                if why:
                    self.refused.add(job); self.log('REFUSED %s: %s' % (job, why))
                    with open(os.path.join(K, 'faults', job + '.refused'), 'a') as f: f.write('%s %s\n' % (utc(), why))
                    continue
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
cat > $K/kit/excl.py.new <<'PYEOF'
"""nvkey scene exclusion assert, loaded by every job builder and by the sender (nvrun.py).
Six protected sets, each pinned by sha256 in K/excl: BENCH v2 (VSI-Bench, ReVSI from REVSI_SCENE_EXCLUSIONS_v1, VSTI, STI-Bench/ReSTI, DSI, OSI,
MindCube; rooms expanded to every capture), dev-S1, R0 (reserve rooms), withheld-80, K1 held-out (K1 manifest k1_split/split != train; teacher list
4d4736cf; the split itself is K1_SPLIT.json, derived from K1_MANIFEST.arkit_timing.json 91a2dbf9). ARKit rooms come from the pinned arkit_3dod_metadata.csv (visit_id). A scene is refused when its capture name or its room is in any set.
usage as a module: import excl; excl.reasons('arkitscenes/41048124') -> []; excl.assert_train(scenes) raises on any hit (label=False skips only
the V1 calibration captures, for calibration jobs).
usage as a script: excl.py -> prints the pins and the set sizes (the V0 receipt)."""
import csv, hashlib, json, os, re, sys
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
E = K + '/excl'
PINS = {'bench_v2': ('benchmark_scene_exclusions.json', '3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'),
        'dev_s1': ('dev_scene_exclusions.json', '969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'),
        'r0': ('R0_ROOMS.txt', 'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'),
        'withheld80': ('WITHHELD_ROOMS_80.json', '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed'),
        'k1_teacher': ('TEACHER_K1.raw', '4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9'),
        'arkit_visits': ('arkit_3dod_metadata.csv', '657020f2d1119220b5068176ffc7298a8585076468407b60d8f5e3e6223442ca'),
        'k1_split': ('K1_SPLIT.json', '8443ff157119f82421cecdf8cd9c8eedb1f42337c46f241427524a749ab5fd59')}
K1_SOURCE_SHA = '91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c'  # K1_MANIFEST.arkit_timing.json, from which K1_SPLIT.json is derived
DS = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes', 'scannetppv2': 'scannetpp', 'scannet++': 'scannetpp', 'scannetpp': 'scannetpp',
      'scannet': 'scannet', 'arkitscenes': 'arkitscenes', 'arkit': 'arkitscenes'}
_S = None
def _read(role):
    name, sha = PINS[role]; raw = open(os.path.join(E, name), 'rb').read()
    assert hashlib.sha256(raw).hexdigest() == sha, 'exclusion list %s differs from its pin' % role
    return raw
def norm(name):
    ds, s = str(name).split('/', 1); d = DS.get(ds.lower())
    if d is None: raise ValueError('unknown dataset prefix in %r' % name)
    return d + '/' + s
def room(canonical, visits=None):
    c = norm(canonical); ds, s = c.split('/', 1)
    if ds == 'scannet':
        m = re.fullmatch(r'(scene\d{4})_\d{2}', s); return 'scannet/' + (m.group(1) if m else s)
    if ds == 'arkitscenes':
        if s.startswith('venue'): return c
        v = (visits or _sets()['visits']).get(s)
        return 'arkitscenes/venue' + v if v and v != 'NA' else c
    return c
def _sets():
    global _S
    if _S is not None: return _S
    visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(_read('arkit_visits').decode().splitlines())}
    S = {'visits': visits, 'names': {}, 'rooms': {}}
    b = json.loads(_read('bench_v2'))
    S['names']['bench_v2'] = {norm(x) for x in b['scenes']}; S['rooms']['bench_v2'] = {norm(x) for x in b['physical_groups']}
    d = json.loads(_read('dev_s1'))
    nm = {norm(x) for x in d['natives']}
    for k in ('canonical', 'aliases'):
        for a, al in d[k].items(): nm.add(norm(a)); nm.update(norm(x) for x in al if not re.fullmatch(r'v[0-9a-f]{12}', x.split('/', 1)[1]))
    S['names']['dev_s1'] = nm; S['rooms']['dev_s1'] = {norm(x) for x in d['rooms'] + d['physical_groups']}
    r0 = [x for x in _read('r0').decode().split() if x]
    S['names']['r0'] = set(); S['rooms']['r0'] = {room(x, visits) for x in r0}
    w = json.loads(_read('withheld80'))
    S['names']['withheld80'] = {norm(x) for al in w['aliases'].values() for x in al if not re.fullmatch(r'v[0-9a-f]{12}', x.split('/', 1)[1])}
    S['rooms']['withheld80'] = {room(x, visits) for x in w['rooms']}
    _read('k1_teacher')
    ks = json.loads(_read('k1_split')); assert ks['source_sha256'] == K1_SOURCE_SHA, 'K1 split source differs'; held = ks['heldout']
    S['names']['k1_heldout'] = {norm(c['canonical']) for c in held}
    S['rooms']['k1_heldout'] = {room(c['canonical'], visits) for c in held} | {norm(c['room']) for c in held if isinstance(c.get('room'), str) and '/' in c['room']}
    S['k1_train'] = {norm(c['canonical']) for c in ks['train']}
    cal = os.path.join(K, 'c1', 'C1_MANIFEST.json')
    S['calibration'] = {norm(v['canonical']) for v in json.load(open(cal)).values()} if os.path.exists(cal) else set()
    _S = S; return S
def reasons(canonical, label=True):
    S = _sets(); c = norm(canonical); r = room(c)
    out = sorted(k for k in S['names'] if c in S['names'][k] or r in S['rooms'][k])
    if c.startswith('arkitscenes/') and not c.split('/', 1)[1].startswith('venue') and c.split('/', 1)[1] not in S['visits']: out.append('no_room_key')
    if label and c in S['calibration']: out.append('v1_calibration')
    return out
def assert_train(scenes, label=True):
    bad = {s: reasons(s, label) for s in scenes}; bad = {s: v for s, v in bad.items() if v}
    if bad: raise AssertionError('protected scenes in a train job: %s' % json.dumps(dict(list(bad.items())[:10])))
    return True
def receipt():
    S = _sets()
    return {'pins': {k: v[1] for k, v in PINS.items()}, 'k1_manifest_sha256': K1_SOURCE_SHA, 'excl_py_sha256': hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest(),
            'names': {k: len(v) for k, v in S['names'].items()}, 'rooms': {k: len(v) for k, v in S['rooms'].items()}, 'k1_train_captures': len(S['k1_train']),
            'v1_calibration_captures': len(S['calibration']),
            'key_granularity': {'bench_v2': 'capture names (every capture of each room) and rooms', 'dev_s1': 'capture names, aliases and rooms', 'r0': 'rooms',
                                'withheld80': 'capture aliases and rooms', 'k1_heldout': 'captures and rooms', 'v1_calibration': 'captures (label jobs only)',
                                'room key': 'ScanNet sceneXXXX over every _NN scan; ARKit venue from arkit_3dod_metadata visit_id (visit NA keeps the video; a video absent from the metadata is refused); ScanNet++ scene id'}}
if __name__ == '__main__':
    print(json.dumps(receipt(), indent=0))
PYEOF
cat > $K/kit/v6_jobs.py.new <<'PYEOF'
"""nvkey2 V6 open-vocabulary inventory, form v2 (consumer spec O2, O5, O6, O10), on K1 TRAINING captures at the 32 anchors.
Primary (one family): named kinds (at most 8 ground-truth classes chosen by sha order), 15 check kinds (frozen list, never chosen by the labeller), and a
blind inventory of up to 40 other instances. States per anchor: L (5% of the frame or more), M (1-5%), S (visible under 1%, cut off, mostly hidden or
unsure), A (not visible); points only on L and M frames. Verifier (second family, chained): the same frames with the named kinds and the primary's
inventory names with counts (no points, no states), plus the check kinds for states only; it returns its own states and points, rejects and missed objects.
usage: v6_jobs.py lists                                     (freeze K/v6/R3_SIBLINGS.json and K/v6/CHECK_VOCAB.json; prints their sha256)
       v6_jobs.py primary OUT.jsonl MODEL EFFORT SELECTION   (SELECTION = first30 | rest | file.json of canonicals)
       v6_jobs.py chain PRIMARY_OUT.jsonl VERIFIER_QUEUE.jsonl MODEL EFFORT   (appends one verifier task per new primary result)"""
import json, os, sys, random, hashlib, collections, sqlite3, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; V6 = K + '/v6'; FORM = 'v6-form-v2'
STORE = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
R3 = [['desk', 'table'], ['door', 'window'], ['cooktop', 'oven', 'stove'], ['cabinet', 'storage cabinet'], ['monitor', 'computer monitor', 'tv'],
      ['chair', 'seat', 'stool', 'office chair', 'armchair'], ['bookshelf', 'shelf', 'bookcase'], ['sofa', 'couch', 'armchair']]
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
STATES = ('Size states: for an object in a frame write L if it is visible and covers 5% of the frame or more, M if it is visible and covers 1% to 5%, '
          'S if it is visible but covers under 1%, is cut off at the frame edge, is mostly hidden, or you are unsure, and A if it is not visible in that frame. '
          'A "states" value is a string of exactly 32 characters from L, M, S, A, one per frame in order (frame 1 first).\n'
          'Points are [x, y] in 0-1000 coordinates of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. '
          'Give points only for frames whose state is L or M.\n')
HEAD = 'These are 32 frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to 32).\n'
PRIMARY = (HEAD + STATES +
           'Task 1, named kinds: {named}. For each kind give "states" (the state of the most visible object of that kind in each frame) and "points" '
           '(for every L or M frame, one point on a visible part of that object).\n'
           'Task 2, check kinds: {check}. Some of these may be in the room and some may not. For each give "states" only.\n'
           'Task 3, inventory: list up to 40 other distinct physical objects visible in these frames (furniture, appliances, fixtures, and objects at least the size '
           'of a book) that are not of the named kinds. An object seen in several frames is one instance; two objects of the same kind are two instances. For each give '
           '"name" (a singular count noun), "aliases" (two other names), "look_alike" (a kind of object it could be mistaken for), "one_object" (true if it is one '
           'physical object), "part_of_larger" (true if it is part of a larger object), "group" (true if it is several objects named as one), "states" and "points" '
           '(on up to 12 of its L or M frames, spread over the video).\n'
           'Reply with one JSON object and nothing else: {{"named": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
           '"check": {{"<kind>": {{"states": "..."}}, ...}}, "inventory": [{{"name": "...", "aliases": ["...", "..."], "look_alike": "...", "one_object": true, '
           '"part_of_larger": false, "group": false, "states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...]}}')
VERIFIER = (HEAD + STATES +
            'Another annotator listed these kinds of objects in this video, with how many distinct objects of each kind it saw: {listed}.\n'
            'For each listed kind give "states" (the state of the most visible object of that kind in each frame) and "points" (for every L or M frame, one point '
            'on a visible part of that object). Then give "rejects": the listed kinds you do not see anywhere in the video, and "missed": other distinct physical '
            'objects (furniture, appliances, fixtures, objects at least the size of a book) that are not of any listed kind, each with "name", "aliases", "states" '
            'and "points" (on up to 12 of its L or M frames).\n'
            'Check kinds, states only (no points): {check}.\n'
            'Reply with one JSON object and nothing else: {{"kinds": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
            '"check": {{"<kind>": {{"states": "..."}}, ...}}, "rejects": ["..."], "missed": [{{"name": "...", "aliases": ["...", "..."], "states": "...", '
            '"points": {{"<frame>": [x, y], ...}}}}, ...]}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1] if l.split() else l; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def lists():
    os.makedirs(V6, exist_ok=True)
    vocab = json.load(open(K + '/excl/TEACHER_K1.raw'))['vocab_by_ds']
    ds = {d: sorted(set(norm(x) for x in v) - STRUCT) for d, v in vocab.items()}
    out = {'R3_SIBLINGS.json': {'form': FORM, 'sets': R3}, 'CHECK_VOCAB.json': {'form': FORM, 'source': 'TEACHER_K1.raw vocab_by_ds (4d4736cf), training vocabularies only', 'datasets': ds,
           'open': sorted(set(x for v in ds.values() for x in v))}}
    for name, v in out.items():
        p = '%s/%s' % (V6, name)
        if not os.path.exists(p): open(p, 'w').write(json.dumps(v, indent=0, sort_keys=True))
        print(name, sha(open(p).read()))
def siblings(l):
    s = {l, head(l)}
    for g in json.load(open(V6 + '/R3_SIBLINGS.json'))['sets']:
        if l in g or head(l) in g: s.update(g); s.update(head(x) for x in g)
    return s
def capture_truth(cn, caps, idx):
    c = caps[cn]; assert c.get('k1_split') == 'train' and c.get('split') == 'train', cn; excl.assert_train([cn])
    z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
    valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]; ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
    big = sorted(set(l for i, l in zip(ids, labels) if l not in STRUCT and any(float((inst[k] == i).sum()) / (H * W) >= 0.01 for k in valid)))
    heads = collections.Counter(head(l) for l in set(labels))
    pool = [l for l in big if l in ALLOW and heads[head(l)] == 1]
    return c, pool, set(labels), big
def build_primary(out, model, effort, selection):
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); c1 = {v['canonical'] for v in json.load(open(K + '/c1/C1_MANIFEST.json')).values()}
    cv = json.load(open(V6 + '/CHECK_VOCAB.json'))
    clear = sorted(cn for cn in idx if cn not in c1 and not excl.reasons(cn))
    if selection in ('first30', 'rest'):
        con = sqlite3.connect('file:%s?mode=ro' % STORE, uri=True); prooms = set()
        for (s,) in con.execute('select row from rows'):
            d = json.loads(s); can = (d.get('provenance') or {}).get('canonical_scene')
            if can and '/' in can:
                try: prooms.add(excl.room(can))
                except Exception: pass
        first = [cn for cn in sorted(clear, key=lambda x: sha('v6 ' + x)) if excl.room(cn) in prooms][:30]
        chosen = first if selection == 'first30' else [cn for cn in clear if cn not in set(first)]
    else: chosen = json.load(open(selection))
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]; n = 0
    with open(out, 'a') as f:
        for cn in chosen:
            c, pool, labels, big = capture_truth(cn, caps, idx)
            named = sorted(pool, key=lambda l: sha(cn + ' ' + l))[:8]
            sib = set().union(*[siblings(l) for l in labels]) if labels else set()
            rng = random.Random('check ' + cn); dsv = cv['datasets'].get(cn.split('/')[0], [])
            absent_ann = [x for x in dsv if x not in labels and x not in sib and head(x) not in sib]; rng.shuffle(absent_ann)
            omitted = [l for l in big if l not in named and not (siblings(l) & set(named))]; rng.shuffle(omitted)
            openv = [x for x in cv['open'] if x not in dsv and x not in sib and head(x) not in sib and x not in STRUCT]; rng.shuffle(openv)
            check = absent_ann[:5] + omitted[:3]; check += [x for x in openv if x not in check][:15 - len(check)]; rng.shuffle(check)
            ctype = {x: ('absent_annotated' if x in absent_ann[:5] else ('present_omitted' if x in omitted[:3] else 'open')) for x in check}
            text = PRIMARY.format(named=json.dumps(named), check=json.dumps(check)); content = [{'text': text}]
            dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]; frames = []
            for k, s in enumerate(slots):
                fs = os.path.basename(dense[s]['path']).split('.')[0]; p = '%s/%s/%s.png' % (FR, fs[:2], fs); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (k + 1)}, {'image': p, 'max_side': 640}]; frames.append({'sha256': fs, 'source_index': int(dense[s]['index'])})
            f.write(json.dumps({'id': 'v6p_%s_%s' % (sha(cn)[:12], mtag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'tag': 'train', 'scenes': [cn], 'form': FORM, 'role': 'primary', 'canonical': cn, 'named': named, 'check': check, 'check_type': ctype,
                                         'frames': frames, 'prompt_sha256': sha(PRIMARY), 'r3_sha256': sha(open(V6 + '/R3_SIBLINGS.json').read()),
                                         'check_vocab_sha256': sha(open(V6 + '/CHECK_VOCAB.json').read())}}) + '\n'); n += 1
    print('v6 primary', mtag, 'captures', len(chosen), 'tasks', n, 'clear pool', len(clear))
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x)):
            try: return json.loads(fix(cand))
            except Exception: pass
    return None
def chain(pout, vq, model, effort):
    done = set()
    if os.path.exists(vq):
        for l in open(vq): done.add(json.loads(l)['meta']['primary_id'])
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]; n = 0
    if not os.path.exists(pout): return 0
    old = open(vq).read() if os.path.exists(vq) else ''; tmp = os.path.join(os.path.dirname(vq), '.' + os.path.basename(vq) + '.tmp')
    with open(tmp, 'w') as f:
        f.write(old)
        for l in open(pout):
            r = json.loads(l)
            if r['id'] in done: continue
            m = r['meta']; d = parse(r['text'])
            inv = [x for x in ((d or {}).get('inventory') or []) if isinstance(x, dict) and x.get('name')] if isinstance(d, dict) else []
            cnt = collections.Counter(norm(x['name']) for x in inv)
            listed = [(k, None) for k in m['named']] + [(k, v) for k, v in sorted(cnt.items()) if k not in m['named']]
            ltxt = ', '.join('%s (%s)' % (k, 'named' if v is None else v) for k, v in listed)
            text = VERIFIER.format(listed=ltxt, check=json.dumps(m['check'])); content = [{'text': text}]
            for k, fr in enumerate(m['frames']):
                p = '%s/%s/%s.png' % (FR, fr['sha256'][:2], fr['sha256']); content += [{'text': 'Frame %d' % (k + 1)}, {'image': p, 'max_side': 640}]
            meta = dict(m, role='verifier', primary_id=r['id'], primary_parsed=d is not None, listed=[k for k, v in listed], counts=dict(cnt), prompt_sha256=sha(VERIFIER))
            f.write(json.dumps({'id': 'v6v_%s_%s' % (sha(m['canonical'])[:12], mtag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                                'content': content, 'meta': meta}) + '\n'); n += 1
    if n: os.replace(tmp, vq)
    return n
if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'lists': lists()
    elif a == 'primary': build_primary(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif a == 'chain': print('chained', chain(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
PYEOF
cat > $K/kit/v1_jobs.py.new <<'PYEOF'
"""nvkey2 V1 batched-form calibration jobs on K1 TRAINING captures (raster truth at the 32 anchors; rasters in K/k1r, frames in /scratch/jjyeung/k1_frames).
Forms: a = guided names (eligible ground-truth classes plus 3 decoys from the dataset's annotated vocabulary that the capture lacks), returning per kind
the visible frames, a point per visible frame, instances with first frames, and a count; b = blind inventory (no names), up to 40 instances with name,
2 aliases, up to 8 clear frames and a point per listed frame. Truth summaries go to K/v1/truth/<alias>.json; masks stay in the rasters (never sent).
usage: v1_jobs.py OUT.jsonl FORM(a|b) MODEL EFFORT NFRAMES(32|64) [CAPS=c1|<n new clear captures>] [max_side=640]"""
import json, os, sys, random, hashlib, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; VIS = 0.002; MAXC = 12
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
PROMPT_A = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
            'Object kinds to look for: {kinds}. Some of these kinds may not be in the room at all.\n'
            'For each kind give:\n'
            '- "frames": every frame number in which at least one object of that kind is visible, fully or partly (partly visible or partly occluded objects count; '
            'reflections and pictures of objects do not);\n'
            '- "points": for each of those frames, one point on a visible part of an object of that kind (if several are visible, the most visible one) as [x, y] '
            'in 0-1000 coordinates of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge;\n'
            '- "instances": the distinct physical objects of that kind seen anywhere in the video, in order of first appearance, each as {{"first_frame": the first '
            'frame number in which that object is visible}}; an object seen again in a later frame is the same instance;\n'
            '- "count": the number of distinct physical objects of that kind in the video (the length of "instances"); 0 if the kind is not in the room.\n'
            'Reply with one JSON object and nothing else, with an entry for every kind listed: '
            '{{"{k0}": {{"frames": [...], "points": {{"<frame>": [x, y], ...}}, "instances": [{{"first_frame": k}}, ...], "count": n}}, ...}}')
PROMPT_B = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
            'Make an inventory of the distinct physical objects visible in these frames: furniture, appliances, fixtures, and other objects at least the size of a book. '
            'List up to 40 objects (instances), larger and clearer ones first. An object seen in several frames is one instance; two objects of the same kind are two instances.\n'
            'For each instance give:\n'
            '- "name": the short noun phrase most people would use for it;\n'
            '- "aliases": two other names a person might use for it;\n'
            '- "frames": up to 8 frame numbers in which it is clearly visible, spread over the video;\n'
            '- "points": for each of those frames, one point on a visible part of that object as [x, y] in 0-1000 coordinates of that frame: x = 0 at the left edge '
            'and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge.\n'
            'Reply with one JSON object and nothing else: {{"instances": [{{"name": "...", "aliases": ["...", "..."], "frames": [...], "points": {{"<frame>": [x, y], ...}}}}, ...]}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def load_ctx():
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); vocab = json.load(open(K + '/excl/TEACHER_K1.raw'))['vocab_by_ds']
    return caps, idx, vocab
def truth(canon, caps, idx, vocab, alias):
    c = caps[canon]; assert c.get('k1_split') == 'train' and c.get('split') == 'train', canon; excl.assert_train([canon])
    z = np.load(K + '/k1r/' + idx[canon]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape; assert n == 32
    missing = [bool(float(z['depth'][k].max()) <= 0) for k in range(32)]
    ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]; heads = collections.Counter(head(l) for l in set(labels))
    area = float(H * W); cls = []
    for l in sorted(set(labels)):
        if l not in ALLOW or heads[head(l)] > 1: continue
        ii = [i for i, x in zip(ids, labels) if x == l]
        per = {i: [float((inst[k] == i).sum()) / area for k in range(32)] for i in ii}
        share = [float(np.isin(inst[k], ii).sum()) / area for k in range(32)]
        if not any(share[k] >= VIS and not missing[k] for k in range(32)): continue
        vis_inst = {i: [k for k in range(32) if per[i][k] >= VIS and not missing[k]] for i in ii}
        firsts = sorted(v[0] for v in vis_inst.values() if v)
        cls.append(dict(name=l, ids=ii, share=share, count=len(firsts), count_any=sum(1 for i in ii if any(per[i][k] > 0 for k in range(32))),
                        first_frames=firsts, nvis=sum(1 for k in range(32) if share[k] >= VIS and not missing[k])))
    cls.sort(key=lambda t: -t['nvis']); cls = cls[:MAXC]
    ds = canon.split('/')[0]; present = set(labels) | set(head(l) for l in labels)
    pool = sorted(v for v in (norm(x) for x in vocab.get(ds, [])) if v in ALLOW and v not in present and head(v) not in present)
    rng = random.Random('decoy ' + canon); decoys = rng.sample(pool, min(3, len(pool)))
    dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]
    sha = lambda p: os.path.basename(p).split('.')[0]
    t = dict(alias=alias, canonical=canon, dataset=ds, raster=idx[canon]['rel'], raster_sha256=idx[canon]['sha256'], H=H, W=W, missing=missing,
             classes=cls, decoys=decoys, anchors=[sha(dense[s]['path']) for s in slots], dense=[sha(f['path']) for f in dense], anchor_slots=slots)
    os.makedirs(K + '/v1/truth', exist_ok=True); json.dump(t, open(K + '/v1/truth/%s.json' % alias, 'w'))
    return t
def main():
    out, form, model, effort, n = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    sel = sys.argv[6] if len(sys.argv) > 6 else 'c1'; side = int(sys.argv[7]) if len(sys.argv) > 7 else 640
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); tag = model.split('/')[-1]
    caps, idx, vocab = load_ctx(); c1 = json.load(open(K + '/c1/C1_MANIFEST.json'))
    if sel == 'c1': chosen = [(a, v['canonical']) for a, v in sorted(c1.items()) if not excl.reasons(v['canonical'])]
    else:
        used = {v['canonical'] for v in c1.values()}; pool = sorted(cn for cn in idx if cn not in used and not excl.reasons(cn))
        chosen = [('k' + hashlib.sha256(cn.encode()).hexdigest()[:11], cn) for cn in random.Random('v1 new').sample(pool, int(sel))]
    nt = 0
    with open(out, 'a') as f:
        for alias, canon in chosen:
            t = truth(canon, caps, idx, vocab, alias)
            shas = t['anchors'] if n == 32 else t['dense']; assert len(shas) == n, (alias, len(shas))
            if form == 'a':
                kinds = [x['name'] for x in t['classes']] + t['decoys']; random.Random('order %s %s' % (alias, n)).shuffle(kinds)
                text = PROMPT_A.format(n=n, kinds=json.dumps(kinds), k0=kinds[0])
            else:
                kinds = None; text = PROMPT_B.format(n=n)
            content = [{'text': text}]
            for i, s in enumerate(shas):
                p = '%s/%s/%s.png' % (FR, s[:2], s); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
            f.write(json.dumps({'id': 'v1%s_%s_%s_f%d' % (form, alias, tag, n), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'tag': 'calibration', 'scenes': [canon], 'alias': alias, 'form': form, 'n': n, 'side': side, 'kinds': kinds,
                                         'prompt_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                         'slots': t['anchor_slots'] if n == 64 else list(range(32))}}) + '\n'); nt += 1
    print('form', form, 'model', tag, 'frames', n, 'captures', len(chosen), 'tasks', nt)
if __name__ == '__main__': main()
PYEOF
cat > $K/kit/v1c_jobs.py.new <<'PYEOF'
"""nvkey2 V1 form (c): judge pointing claims with a ring on the 640-px frame plus a 256-px close-up crop (ring drawn) of every point claim; 24 claims per call.
Rows: pilot = the 1,208 pointing-store rows with local frames (all dev-S1: tag dev-analysis); nearmiss = 300 claims built from K1 TRAINING rasters with known
truth (100 true points, 50 points just off the object, 50 wrong names, 50 true absent, 50 false absent; objects at 1% of the frame or more): tag train.
Verdicts: point rows on | off | wrong_name | absent | unsure; absent rows absent | visible | unsure. Crops are pre-rendered to K/v1/crops (never truth).
usage: v1c_jobs.py OUT.jsonl SET(pilot|nearmiss) MODEL EFFORT [CHUNK=24]"""
import json, os, sys, random, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; CR = K + '/v1/crops'
PROMPT = ('You are auditing the labels of a pointing dataset. Each row below shows one video frame of an indoor room and one claim about it.\n'
          '- A point row shows the frame with a red ring, then a close-up crop of the same frame around the ring (the ring is drawn there too). '
          'Its claim: the centre of the ring lies on a visible part of an object of the named kind.\n'
          '- An absent row shows the frame only. Its claim: no object of the named kind is visible anywhere in the frame.\n'
          'Judge every claim from its own images. Give one verdict per row:\n'
          'point rows: "on" (the ring centre lies on a visible part of an object of the named kind), "off" (an object of the named kind is visible in the frame, '
          'but the ring centre is not on it), "wrong_name" (the ring centre is on an object that most people would not call by the named kind or a close synonym, '
          'and no object of that kind is under the ring), "absent" (no object of the named kind is visible anywhere in the frame), or "unsure";\n'
          'absent rows: "absent" (the claim holds), "visible" (an object of the named kind is visible in the frame), or "unsure".\n'
          'Reply with one JSON object and nothing else: {{"<row id>": "<verdict>", ...}} with all {n} row ids.')
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def crop(path, uv, rid):
    os.makedirs(CR, exist_ok=True); out = '%s/%s.png' % (CR, rid)
    if os.path.exists(out): return out
    im = Image.open(path).convert('RGB'); W, H = im.size; x, y = uv[0] / 1000.0 * W, uv[1] / 1000.0 * H; s = 0.4 * min(W, H)
    x0 = min(max(0.0, x - s / 2), W - s); y0 = min(max(0.0, y - s / 2), H - s)
    c = im.crop((int(x0), int(y0), int(x0 + s), int(y0 + s))).resize((256, 256), Image.LANCZOS)
    px, py = (x - int(x0)) * 256.0 / s, (y - int(y0)) * 256.0 / s; d = ImageDraw.Draw(c); r = 12
    for rr, col in ((r + 2, (0, 0, 0)), (r, (255, 0, 0)), (r - 2, (0, 0, 0))): d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col, width=2)
    c.save(out); return out
def nearmiss_rows():
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); c1 = {v['canonical'] for v in json.load(open(K + '/c1/C1_MANIFEST.json')).values()}
    pool = sorted(cn for cn in idx if cn not in c1 and not excl.reasons(cn)); rng = random.Random('v1c nearmiss'); rng.shuffle(pool)
    want = collections.OrderedDict([('true_point', 100), ('off', 50), ('wrong_name', 50), ('true_absent', 50), ('false_absent', 50)]); got = collections.Counter(); rows = []
    for cn in pool:
        if all(got[k] >= v for k, v in want.items()): break
        c = caps[cn]; z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]; ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
        heads = collections.Counter(head(l) for l in set(labels)); cls = [l for l in sorted(set(labels)) if l in ALLOW and heads[head(l)] == 1]
        if len(cls) < 2: continue
        masks = {l: np.isin(inst, [i for i, x in zip(ids, labels) if x == l]) for l in cls}; share = {l: masks[l].reshape(32, -1).mean(1) for l in cls}
        sha = lambda k: os.path.basename(c['dense_frames'][int(c['anchor_slots'][k])]['path']).split('.')[0]
        uv = lambda yx: [round((yx[1] + 0.5) / W * 1000), round((yx[0] + 0.5) / H * 1000)]
        per = 0
        for _ in range(40):
            if per >= 14: break
            kind = rng.choice([k for k in want if got[k] < want[k]] or ['none'])
            if kind == 'none': break
            l = rng.choice(cls); big = [k for k in valid if share[l][k] >= 0.01]; zero = [k for k in valid if share[l][k] == 0]
            if kind in ('true_point', 'off', 'wrong_name', 'false_absent') and not big: continue
            if kind == 'true_absent' and (not zero or not big): continue
            k = rng.choice(zero if kind == 'true_absent' else big); m = masks[l][k]; row = dict(canonical=cn, frame=k, sha=sha(k), share=float(share[l][k]), type=kind)
            if kind in ('true_point', 'wrong_name'):
                er = m.copy()
                for _e in range(3): er = er & np.roll(er, 1, 0) & np.roll(er, -1, 0) & np.roll(er, 1, 1) & np.roll(er, -1, 1)
                pts = np.argwhere(er)
                if not len(pts): continue
                p = pts[rng.randrange(len(pts))]; row['uv'] = uv(p)
                if kind == 'wrong_name':
                    others = [o for o in cls if o != l and not masks[o][k][p[0], p[1]] and head(o) != head(l)]
                    if not others: continue
                    row['label'] = rng.choice(others); row['true_label'] = l; row['label_visible_in_frame'] = bool(share[row['label']][k] > 0)
                else: row['label'] = l
                row['kind'] = 'point'
            elif kind == 'off':
                any_l = m; dil = m.copy()
                for _e in range(10): dil = dil | np.roll(dil, 1, 0) | np.roll(dil, -1, 0) | np.roll(dil, 1, 1) | np.roll(dil, -1, 1)
                ring = dil & ~m
                for _e in range(3): ring = ring & ~(np.roll(m, _e + 1, 0) | np.roll(m, -_e - 1, 0) | np.roll(m, _e + 1, 1) | np.roll(m, -_e - 1, 1))
                pts = np.argwhere(ring)
                if not len(pts): continue
                p = pts[rng.randrange(len(pts))]; row.update(uv=uv(p), label=l, kind='point')
            else: row.update(label=l, kind='absent')
            row['id'] = 'n' + hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:10]
            row['path'] = '%s/%s/%s.png' % (FR, row['sha'][:2], row['sha']); assert os.path.isfile(row['path'])
            rows.append(row); got[kind] += 1; per += 1
    os.makedirs(K + '/v1', exist_ok=True); json.dump(rows, open(K + '/v1/NEARMISS_TRUTH.json', 'w'))
    print('nearmiss rows', len(rows), dict(got), 'captures', len(set(r['canonical'] for r in rows)))
    return rows
def pilot_rows():
    import c2_jobs
    rows, _ = c2_jobs.load_rows(None); out = []
    for r in rows:
        can = r['canonical'] or '%s/%s' % (r['dataset'], r['scene'])
        out.append(dict(id='r%d' % r['i'], canonical=can, path=r['path'], uv=r['uv'], label=r['label'], kind='absent' if r['kind'] == 'gt_absent' else 'point', scene=r['scene']))
    return out
def main():
    out, which, model, effort = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]; chunk = int(sys.argv[5]) if len(sys.argv) > 5 else 24
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]
    if which == 'nearmiss':
        p = K + '/v1/NEARMISS_TRUTH.json'; rows = json.load(open(p)) if os.path.exists(p) else nearmiss_rows(); tag = 'calibration'
        excl.assert_train(sorted(set(r['canonical'] for r in rows)), label=False)
    else:
        rows = pilot_rows(); tag = 'dev-analysis'
        assert all(excl.reasons(r['canonical']) for r in rows), 'a pilot row outside the protected sets: build it as a train job'
    by = collections.defaultdict(list)
    for r in rows: by[r['canonical']].append(r)
    rng = random.Random('v1c ' + which); n = 0
    with open(out, 'a') as f:
        groups = []
        for cn in sorted(by):
            rs = by[cn][:]; rng.shuffle(rs); groups += [rs[j:j + chunk] for j in range(0, len(rs), chunk)]
        if which == 'nearmiss':
            flat = [r for g in groups for r in g]; groups = [flat[j:j + chunk] for j in range(0, len(flat), chunk)]
        for gi, part in enumerate(groups):
            text = PROMPT.format(n=len(part)); content = [{'text': text}]
            for r in part:
                if r['kind'] == 'absent':
                    content += [{'text': 'Row %s (absent row): kind = "%s"' % (r['id'], r['label'])}, {'image': r['path'], 'max_side': 640}]
                else:
                    content += [{'text': 'Row %s (point row): kind = "%s"' % (r['id'], r['label'])}, {'image': r['path'], 'max_side': 640, 'mark': r['uv']},
                                {'text': 'Row %s close-up' % r['id']}, {'image': crop(r['path'], r['uv'], r['id']), 'max_side': 256}]
            f.write(json.dumps({'id': 'v1c_%s_%03d_%s' % (which, gi, mtag), 'model': model, 'effort': effort, 'max_tokens': 16384, 'extra': extra, 'content': content,
                                'meta': {'tag': tag, 'scenes': sorted(set(r['canonical'] for r in part)), 'set': which, 'rows': [r['id'] for r in part],
                                         'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}}) + '\n'); n += 1
    print(which, mtag, 'rows', len(rows), 'tasks', n)
if __name__ == '__main__': main()
PYEOF
cat > $K/kit/v2_jobs.py.new <<'PYEOF'
"""nvkey2 V2 alias table: numbered crops of K1 TRAINING ground-truth instances (the anchor frame with the largest mask share, 20% context around the
instance box, mask outline drawn, no class name), 30 crops per call. Returns per crop five noun phrases, the noun a question writer would use, a
part-of-larger flag and a one-object flag. Instances: every ground-truth instance at 1% of the frame or more in some valid anchor of the clear K1
training captures (exclusion assert), rarest classes first. Crops go to K/v2/crops; the instance index (truth) to K/v2/INSTANCES.json (never sent).
usage: v2_jobs.py OUT.jsonl MODEL EFFORT [PER_CALL=30] [all | N | calN (seeded random calibration sample) | restN (all but that sample)]"""
import json, os, sys, random, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; CR = K + '/v2/crops'
PROMPT = ('Below are {n} numbered crops from photos of indoor rooms. In each crop one object is outlined in green. Name the outlined object only.\n'
          'For each crop give:\n'
          '- "phrases": five different noun phrases a person might use for the outlined object, most likely first (for example "office chair", "desk chair", '
          '"swivel chair", "chair", "rolling chair");\n'
          '- "question_noun": the single noun phrase a person writing a question about this room would most likely use for it;\n'
          '- "part_of_larger": true if the outline covers only a part of a larger object (for example a drawer of a cabinet or a door of a wardrobe), else false;\n'
          '- "one_object": true if the outline covers exactly one physical object, false if it covers several objects or none.\n'
          'Reply with one JSON object and nothing else: {{"1": {{"phrases": [...], "question_noun": "...", "part_of_larger": false, "one_object": true}}, ..., "{n}": {{...}}}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def instances():
    p = K + '/v2/INSTANCES.json'
    if os.path.exists(p): return json.load(open(p))
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); out = []
    for cn in sorted(idx):
        if excl.reasons(cn): continue
        c = caps[cn]; assert c.get('k1_split') == 'train' and c.get('split') == 'train'
        z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]
        for i, lab in zip([int(x) for x in z['ids']], [norm(x) for x in z['labels']]):
            sh = [(float((inst[k] == i).sum()) / (H * W), k) for k in valid]
            if not sh: continue
            s, k = max(sh)
            if s < 0.01: continue
            ys, xs = np.nonzero(inst[k] == i)
            sha = os.path.basename(c['dense_frames'][int(c['anchor_slots'][k])]['path']).split('.')[0]
            out.append(dict(id='i' + hashlib.sha256(('%s %d' % (cn, i)).encode()).hexdigest()[:10], canonical=cn, dataset=cn.split('/')[0], inst=i, label=lab,
                            frame=k, share=round(s, 4), box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], H=H, W=W, sha=sha, raster=idx[cn]['rel']))
    freq = collections.Counter(x['label'] for x in out)
    random.Random('v2').shuffle(out); out.sort(key=lambda x: freq[x['label']])
    os.makedirs(K + '/v2', exist_ok=True); json.dump(out, open(p, 'w'))
    print('instances', len(out), 'captures', len(set(x['canonical'] for x in out)), 'labels', len(freq))
    return out
def crop(x):
    os.makedirs(CR, exist_ok=True); out = '%s/%s.png' % (CR, x['id'])
    if os.path.exists(out): return out
    im = Image.open('%s/%s/%s.png' % (FR, x['sha'][:2], x['sha'])).convert('RGB'); Wf, Hf = im.size; sx, sy = Wf / float(x['W']), Hf / float(x['H'])
    z = np.load(K + '/k1r/' + x['raster'], allow_pickle=True); m = (z['inst'][x['frame']] == x['inst'])
    x0, y0, x1, y1 = x['box']; bw, bh = x1 - x0 + 1, y1 - y0 + 1; cx0 = max(0, x0 - 0.2 * bw); cy0 = max(0, y0 - 0.2 * bh); cx1 = min(x['W'], x1 + 1 + 0.2 * bw); cy1 = min(x['H'], y1 + 1 + 0.2 * bh)
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    big = im.copy(); d = ImageDraw.Draw(big)
    for yy, xx in np.argwhere(edge):
        d.rectangle([xx * sx - 1, yy * sy - 1, (xx + 1) * sx, (yy + 1) * sy], fill=(0, 255, 0))
    c = big.crop((int(cx0 * sx), int(cy0 * sy), int(cx1 * sx), int(cy1 * sy))); s = 256.0 / max(c.size)
    if s < 1: c = c.resize((max(1, int(c.size[0] * s)), max(1, int(c.size[1] * s))), Image.LANCZOS)
    c.save(out); return out
def main():
    out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; per = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    lim = sys.argv[5] if len(sys.argv) > 5 else 'all'; effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]
    xs = instances()
    if lim.startswith('cal'): xs = random.Random('v2 cal').sample(xs, int(lim[3:]))
    elif lim.startswith('rest'):
        cal = {x['id'] for x in random.Random('v2 cal').sample(xs, int(lim[4:]))}; xs = [x for x in xs if x['id'] not in cal]
    elif lim != 'all': xs = xs[:int(lim)]
    if not lim.startswith('cal'): xs = [x for x in xs if not excl.reasons(x['canonical'])]
    excl.assert_train(sorted(set(x['canonical'] for x in xs)), label=not lim.startswith('cal')); n = 0
    with open(out, 'a') as f:
        for j in range(0, len(xs), per):
            part = xs[j:j + per]; text = PROMPT.format(n=len(part)); content = [{'text': text}]
            for q, x in enumerate(part): content += [{'text': 'Crop %d' % (q + 1)}, {'image': crop(x), 'max_side': 256}]
            f.write(json.dumps({'id': 'v2_%04d_%s' % (j // per, mtag), 'model': model, 'effort': effort, 'max_tokens': 16384, 'extra': extra, 'content': content,
                                'meta': {'tag': 'calibration' if lim.startswith('cal') else 'train', 'scenes': sorted(set(x['canonical'] for x in part)), 'items': [x['id'] for x in part],
                                         'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}}) + '\n'); n += 1
    print('v2', mtag, 'instances', len(xs), 'tasks', n)
if __name__ == '__main__': main()
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/5*.jsonl analysis_only/out/5*.jsonl 2>/dev/null | tail -7
for f in nvrun.py excl.py v6_jobs.py v1_jobs.py v1c_jobs.py v2_jobs.py; do mv kit/$f.new kit/$f; done
$P -B kit/excl.py | tr -d '\n' | cut -c1-600; echo
$P -B kit/v6_jobs.py lists
$P -B kit/v6_jobs.py primary queue/.45.tmp gcp/google/gemini-4-argon high first30 && mv queue/.45.tmp queue/45_v6p30.jsonl
$P -B - <<'PY'
import json, os
for j in ('50_v1a32', '52_v1b32', '54_v1c_nearmiss', '55_v2cal'):
    p = 'queue/%s.jsonl' % j; ts = [json.loads(l) for l in open(p)]
    for t in ts: t['meta']['tag'] = 'calibration'
    open(p + '.tmp', 'w').write(''.join(json.dumps(t) + '\n' for t in ts)); os.replace(p + '.tmp', p); print('retagged', j, len(ts))
t = json.loads(open('queue/45_v6p30.jsonl').readline()); m = t['meta']; print('v6p', m['canonical'], m['named'], m['check'], m['check_type'], m['prompt_sha256'][:16], len(t['content']))
import sys; sys.path.insert(0, 'kit'); import excl
ts = [json.loads(l) for l in open('queue/45_v6p30.jsonl')]; print('v6 first30 reasons', [excl.reasons(x['meta']['canonical']) for x in ts][:3], len(ts), sorted(set(x['meta']['canonical'].split('/')[0] for x in ts)))
PY
mv queue/51_v1a64.jsonl queue_done/51_v1a64.partial.jsonl
tmux kill-session -t nvk1_run 2>/dev/null; sleep 1
tmux new-session -d -s nvk1_run "cd $K && SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt NVK=$K /scratch/jjyeung/envs/p1cpu/bin/python -B kit/nvrun.py 3600 </dev/null >>$K/runner.stdout 2>&1" </dev/null >/dev/null 2>&1
tmux kill-session -t nvk2_chain 2>/dev/null
tmux new-session -d -s nvk2_chain "cd $K && for i in \$(seq 1 600); do NVK=$K $P -B kit/v6_jobs.py chain out/45_v6p30.jsonl queue/46_v6v30.jsonl openai/openai/gpt-6.2-astra high >> $K/v6/chain.log 2>&1; sleep 60; done </dev/null >/dev/null 2>&1" </dev/null >/dev/null 2>&1
sleep 25; tmux ls | grep nvk; tail -8 runner.log; tail -3 runner.stdout
