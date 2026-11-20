#!/usr/bin/env python3
"""Orchard NV runner of lane nv_orch1 (CPU batch job on the preempt partition). Derived from nvkey1 nvrun_o.py.
Images: {"image": "tar:<sha256>"} resolves through the header index of the tar files named in env NVO_TARS (colon-separated).
Stops also at K/ALLOC.md (mirror pushed from Trinity) lines "STOP nv_orch1" or new BLOCK lines, and at the send deadline 2026-11-21T03:30Z.
Jobs: K/queue/<prio>_<job>.jsonl, one task per line:
  {"id": str, "model": "<route id>", "effort": "high"|"medium"|null, "max_tokens": int,
   "content": [{"text": str} | {"image": "/abs/frame.png", "max_side": 640, "mark": [u, v] (0-1000 grid, optional)}],
   "meta": {...}}
Results: K/out/<job>.jsonl, one line per finished task (id, model, served, text, usage, dollars, ...). Finished ids are skipped on restart.
Control files in K/ctl: RATE (requests per minute, 5-minute mean, default 4), INFLIGHT (default 8), BPS (upload bytes/s, default 1.5e6),
BUDGET (dollars at list price over all calls in K/meter/CALLS.jsonl, default 0 = send nothing), STOP. Every call is logged in K/meter/CALLS.jsonl.
Stops before the next call: K/ctl/STOP, K/ev/STOP, a K/ALLOC.md line 'STOP nv_orch1', any BLOCK line or Think3D r3243-r3245 line in
ALLOC.md written after the runner started, the budget reached, the deadline, or a WAF 429 (then it writes K/ev/WAF429 for the lane to relay and exits).
A 429 without WAF header or a 503 halves RATE and INFLIGHT and stops the runner for the lane to decide. A reply whose served model differs from the request is a fault.
Keys come only from the environment (NVK_A..NVK_D, passed at sbatch submission); they are popped at start and never printed or written.
Tags (as nvkey2's nvrun v2): every task carries meta.tag in train | dev-analysis | eval, one tag per job. A train job is refused whole unless every task
carries meta.scenes_h (sha256 of each canonical capture name and room) and none is in K/excl/DENY.sha256 (pinned by K/excl/DENY.pin; the hashed
union of nvkey2's six exclusion lists, built on Trinity with excl.py). dev-analysis results go to K/analysis_only/out/<job>.jsonl; eval jobs run only
while K/ctl/EVAL_OK exists. BUDGET_PROXY stops on proxy-reported dollars like BUDGET on list dollars.
Chains: a task with meta.chain = {"job": J2} hands its finished result to K/kit/forms.py chain(task, result) -> list of follow-up tasks, which are
appended to K/queue/<J2>.jsonl (the verifier of a paired form)."""
import base64, glob, hashlib, io, json, os, re, sys, threading, time, traceback, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

K = os.environ['NVO']
EV = os.path.join(K, 'ev')
ALLOC = os.path.join(K, 'ALLOC.md')  # mirrored from Trinity by the lane; a BLOCK or STOP line there stops this runner
DEADLINE = 1795231800.0  # 2026-11-21T03:30:00Z: no request starts after this
URL = os.environ.get('NVO_URL', 'https://inference-api.nvidia.com/v1/chat/completions')
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
    names = ['NVK_A', 'NVK_B', 'NVK_C', 'NVK_D']
    keys = [os.environ.pop(n) for n in names if os.environ.get(n)]
    assert keys, 'no NV key in the environment'
    return keys

TAR_INDEX = {}; TAR_LOCK = threading.Lock()
def tar_bytes(sha):
    import tarfile
    with TAR_LOCK:
        if not TAR_INDEX and os.environ.get('NVO_INDEX'):
            import gzip
            for p in os.environ['NVO_INDEX'].split(':'):
                for l in gzip.open(p, 'rt'):
                    h, tp, off, size = l.rstrip('\n').split('\t'); TAR_INDEX[h] = (tp, int(off), int(size))
        if not TAR_INDEX:
            for tp in [t for t in os.environ.get('NVO_TARS', '').split(':') if t]:
                with tarfile.open(tp, 'r:') as tf:
                    for m in tf:
                        if m.isfile(): TAR_INDEX[os.path.basename(m.name).split('.')[0]] = (tp, m.offset_data, m.size)
    tarp, off, size = TAR_INDEX[sha]
    with open(tarp, 'rb') as f:
        f.seek(off); b = f.read(size)
    assert hashlib.sha256(b).hexdigest() == sha, 'frame sha mismatch ' + sha
    return b

def rint(name, default, cast=float):
    try: return cast(open(os.path.join(K, 'ctl', name)).read().strip())
    except Exception: return default

def utc(t=None): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t if t is not None else time.time()))

def crop_v1c(im, uv):
    # nvkey2 v1c_jobs.crop, verbatim geometry: side 0.4 x short side, resized to 256 px, ring radius 12 px drawn after the resize
    W, H = im.size; x, y = uv[0] / 1000.0 * W, uv[1] / 1000.0 * H; s = 0.4 * min(W, H)
    x0 = min(max(0.0, x - s / 2), W - s); y0 = min(max(0.0, y - s / 2), H - s)
    c = im.crop((int(x0), int(y0), int(x0 + s), int(y0 + s))).resize((256, 256), Image.LANCZOS)
    px, py = (x - int(x0)) * 256.0 / s, (y - int(y0)) * 256.0 / s; d = ImageDraw.Draw(c); r = 12
    for rr, col in ((r + 2, (0, 0, 0)), (r, (255, 0, 0)), (r - 2, (0, 0, 0))): d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col, width=2)
    return c

def encode_image(path, max_side=640, mark=None, quality=90, crop=None, cropv1c=None):
    src = io.BytesIO(tar_bytes(path[4:])) if path.startswith('tar:') else path
    im = Image.open(src).convert('RGB')
    if cropv1c is not None: im = crop_v1c(im, cropv1c)
    w, h = im.size
    if crop is not None:  # [u, v, side]: a side x side px window of the native frame centred on (u, v) in the 0-1000 grid; the mark moves with it
        cx, cy, side = crop[0] / 1000.0 * w, crop[1] / 1000.0 * h, int(crop[2])
        x0 = int(min(max(0, cx - side / 2), max(0, w - side))); y0 = int(min(max(0, cy - side / 2), max(0, h - side)))
        im = im.crop((x0, y0, x0 + min(side, w), y0 + min(side, h)))
        if mark is not None: mark = [(mark[0] / 1000.0 * w - x0) / im.size[0] * 1000.0, (mark[1] / 1000.0 * h - y0) / im.size[1] * 1000.0]
        w, h = im.size
    s = min(1.0, float(max_side) / max(w, h))
    if s < 1.0: im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    if mark is not None:
        W, H = im.size; x, y = mark[0] / 1000.0 * W, mark[1] / 1000.0 * H; d = ImageDraw.Draw(im); r = max(6, round(0.018 * max(W, H)))
        for rr, col in ((r + 2, (0, 0, 0)), (r, (255, 0, 0)), (r - 2, (0, 0, 0))):
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col, width=2)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=quality); jb = b.getvalue()
    return 'data:image/jpeg;base64,' + base64.b64encode(jb).decode(), im.size, hashlib.sha256(jb).hexdigest()

class Runner:
    def __init__(self):
        for d in ('queue', 'out', 'meter', 'ctl', 'faults', 'analysis_only/out'): os.makedirs(os.path.join(K, d), exist_ok=True)
        self.refused = set(); self.qlock = threading.Lock()
        self.keys = load_keys(); self.kidx = 0; self.lock = threading.Lock(); self.starts = []; self.inflight = 0
        self.t0 = time.time(); self.bytes_tokens = 0.0; self.bytes_t = time.time(); self.stop_reason = None
        self.spent = 0.0; self.proxy = 0.0; self.calls = 0; self.backoff_until = 0.0; self.alloc_seen = self._alloc_len(); self.last_check = 0.0
        self.spent, self.proxy = self._meter_spend(); self.mlock = threading.Lock(); self.model_faults = {}; self.bad_models = set()
        self.meter = open(os.path.join(K, 'meter', 'CALLS.jsonl'), 'a')
        self.log('start spent %.4f keys %d' % (self.spent, len(self.keys)))

    def mwrite(self, rec):
        with self.mlock:
            self.meter.write(json.dumps(rec) + '\n'); self.meter.flush()

    def _meter_spend(self):
        s = 0.0; p = 0.0
        try:
            for l in open(os.path.join(K, 'meter', 'CALLS.jsonl')):
                try: r = json.loads(l); s += r.get('dollars', 0.0) or 0.0; p += float(r.get('header_cost') or 0.0)
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
                if 'STOP nv_orch1' in l and 'stops me' not in l: self.stop_reason = 'ALLOC STOP nv_orch1'
            for l in lines[self.alloc_seen:]:
                if re.match(r'^\S+\s+BLOCK\b', l): self.stop_reason = 'ALLOC BLOCK: ' + l[:120]
                if re.search(r'r324[345]|think3d', l, re.I) and re.search(r'HOLD|START|LAUNCH|GATE', l): self.stop_reason = 'ALLOC Think3D: ' + l[:120]
        except OSError: pass
        if self.spent >= rint('BUDGET', 0.0): self.stop_reason = 'budget %.2f reached' % self.spent
        if now >= DEADLINE: self.stop_reason = 'send deadline 2026-11-21T03:30Z'
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
        content = []; sizes = []; sent = []
        for c in task['content']:
            if 'text' in c: content.append({'type': 'text', 'text': c['text']})
            else:
                url, sz, jsha = encode_image(c['image'], c.get('max_side', 640), c.get('mark'), crop=c.get('crop'), cropv1c=c.get('crop_v1c'))
                content.append({'type': 'image_url', 'image_url': {'url': url, 'detail': 'high'}}); sizes.append(sz)
                sent.append({'src': c['image'], 'jpeg_sha256': jsha, 'size': list(sz), 'max_side': c.get('max_side', 640), 'crop': c.get('crop'), 'crop_v1c': c.get('crop_v1c'), 'mark': c.get('mark'), 'q': 90})
        body = {'model': task['model'], 'messages': [{'role': 'user', 'content': content}], 'max_tokens': task.get('max_tokens', 16384)}
        if task.get('effort'): body['reasoning_effort'] = task['effort']
        body.update(task.get('extra') or {})
        return body, sizes, sent

    def run_task(self, job, task, outf, olock):
        if task['model'] in self.bad_models:
            with open(os.path.join(K, 'faults', job + '.gaveup.jsonl'), 'a') as f: f.write(json.dumps({'id': task['id'], 'utc': utc(), 'why': 'model faulted'}) + '\n')
            return
        try: body, sizes, sent_imgs = self.build(task)
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
                    self.stop_reason = 'HTTP %s on the second source: stopped for the lane to decide' % status
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
                   'header_cost': hcost, 'secs': rec['secs'], 'sizes': sizes, 'sent': sent_imgs, 'litellm_model_id': rec.get('litellm_model_id'), 'meta': task.get('meta', {})}
            with olock:
                outf.write(json.dumps(out) + '\n'); outf.flush()
            ch = (task.get('meta') or {}).get('chain')
            if ch and rec['finish'] == 'stop':
                try:
                    sys.path.insert(0, os.path.join(K, 'kit')); import forms
                    nxt = forms.chain(task, out)
                    if nxt:
                        with self.qlock, open(os.path.join(K, 'queue', ch['job'] + '.jsonl'), 'a') as qf:
                            for t in nxt: qf.write(json.dumps(t) + '\n')
                except Exception as e:
                    self.log('CHAIN FAIL %s %s %r' % (job, task['id'], e))
            return
        self.log('GAVE UP %s %s' % (job, task['id']))
        with open(os.path.join(K, 'faults', job + '.gaveup.jsonl'), 'a') as f: f.write(json.dumps({'id': task['id'], 'utc': utc()}) + '\n')

    def waf(self, rec):
        self.stop_reason = 'WAF 429'
        with self.lock:
            rate5 = len([t for t in self.starts if time.time() - t < 300]) / 5.0
        os.makedirs(EV, exist_ok=True)
        open(os.path.join(EV, 'WAF429'), 'a').write('%s WAF 429 job %s at %.1f requests/min (5-min mean, Orchard runner)\n' % (rec['utc'], rec['job'], rate5))
        self.log('WAF 429 -> stopped')

    def write_meter(self):
        now = time.time()
        with self.lock: r5 = len([t for t in self.starts if now - t < 300]) / 5.0; infl = self.inflight
        m = {'utc': utc(), 'lane': 'nv_orch1', 'job': os.environ.get('SLURM_JOB_ID'), 'proxy_total': round(self.proxy, 4), 'host': os.uname()[1], 'req_min5': round(r5, 2), 'inflight': infl, 'rate_target': rint('RATE', 4.0),
             'dollars_list_total': round(self.spent, 4), 'calls_this_run': self.calls, 'stop_reason': self.stop_reason}
        try:
            tmp = os.path.join(K, 'meter', '.METER.json.tmp'); open(tmp, 'w').write(json.dumps(m) + '\n'); os.replace(tmp, os.path.join(K, 'meter', 'METER.json'))
        except OSError: pass

    def gate(self, job, tasks, tags):
        if len(tags) != 1 or not tags <= {'train', 'dev-analysis', 'eval'}: return 'tags %r: one of train, dev-analysis, eval per job' % sorted(map(str, tags))
        tag = next(iter(tags))
        if tag == 'eval' and not os.path.exists(os.path.join(K, 'ctl', 'EVAL_OK')): return 'eval job without ctl/EVAL_OK'
        if tag == 'train':
            if not all((t.get('meta') or {}).get('scenes_h') for t in tasks): return 'train task without meta.scenes_h'
            deny = set()
            for name in ['DENY'] + (['DENY_K1'] if any((t.get('meta') or {}).get('deny_k1') for t in tasks) else []):
                try:
                    raw = open(os.path.join(K, 'excl', name + '.sha256'), 'rb').read(); pin = open(os.path.join(K, 'excl', name + '.pin')).read().split()[0]
                except OSError as e: return 'no exclusion list %s: %r' % (name, e)
                if hashlib.sha256(raw).hexdigest() != pin: return 'exclusion list %s differs from its pin' % name
                deny |= set(raw.decode().split())
            hits = sorted(set(h for t in tasks for h in t['meta']['scenes_h'] if h in deny))
            if hits: return 'exclusion assert: %d protected scene hashes, e.g. %s' % (len(hits), hits[:3])
        return None

    def jobs(self):
        return sorted(glob.glob(os.path.join(K, 'queue', '*.jsonl')))

    def main(self, idle_exit=1800):
        ex = ThreadPoolExecutor(max_workers=int(os.environ.get('NVO_WORKERS', '48'))); pending = {}; idle_since = time.time(); last_meter = 0
        while True:
            if time.time() - last_meter > 60: self.write_meter(); last_meter = time.time()
            if self.check_stops():
                self.log('STOP: %s' % self.stop_reason); break
            submitted = False
            for qf in self.jobs():
                job = os.path.basename(qf)[:-6]
                if job in self.refused or (job in pending and pending[job]): continue
                with self.qlock: tasks = [json.loads(l) for l in open(qf) if l.strip()]
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
