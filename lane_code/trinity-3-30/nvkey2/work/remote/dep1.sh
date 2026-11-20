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
Stops before the next call: K/ctl/STOP, B/events/nvkey/STOP, an ALLOC.md line 'STOP nvkey1', any BLOCK line or Think3D r3243-r3245 line in
ALLOC.md written after the runner started, the budget reached, or a WAF 429 (then it appends BLOCK to ALLOC.md and exits).
A 429 without WAF header or a 503 backs off and halves RATE and INFLIGHT. A reply whose served model differs from the request is a fault.
Keys come from the environment (NV_INFERENCE_API_KEY, _KEY2.._KEY4) or the export lines of ~/.bashrc; they are never printed or written.
Tags (nvkey2): every task of a job with work left carries meta.tag in train | dev-analysis | eval and meta.scenes (canonical names). A train job
whose scenes hit kit/excl.py (six hashed exclusion lists) is refused whole; dev-analysis results go to K/analysis_only/out/<job>.jsonl; eval jobs
run only while K/ctl/EVAL_OK exists. BUDGET_PROXY (proxy-reported dollars, the working figure) stops the runner like BUDGET (list dollars)."""
import base64, glob, io, json, os, re, sys, threading, time, traceback, urllib.request, urllib.error
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
    b = io.BytesIO(); im.save(b, 'JPEG', quality=quality)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode(), im.size

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
                if 'STOP nvkey1' in l and 'stops me' not in l: self.stop_reason = 'ALLOC STOP nvkey1'
            for l in lines[self.alloc_seen:]:
                if ' BLOCK' in l and 'nvkey1' not in l: self.stop_reason = 'ALLOC BLOCK: ' + l[:120]
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
        m = {'utc': utc(), 'lane': 'nvkey2', 'host': os.uname()[1], 'req_min5': round(r5, 2), 'inflight': infl, 'rate_target': rint('RATE', 4.0),
             'dollars_list_total': round(self.spent, 4), 'dollars_proxy_total': round(self.proxy, 4), 'calls_this_run': self.calls, 'stop_reason': self.stop_reason}
        try:
            tmp = os.path.join(EV, '.METER.json.tmp'); open(tmp, 'w').write(json.dumps(m) + '\n'); os.replace(tmp, os.path.join(EV, 'METER.json'))
        except OSError: pass
        open(os.path.join(K, 'meter', 'METER.json'), 'w').write(json.dumps(m) + '\n')

    def gate(self, job, tasks, tags):
        if len(tags) != 1 or not tags <= {'train', 'dev-analysis', 'eval'}: return 'tags %r: one of train, dev-analysis, eval per job' % sorted(map(str, tags))
        tag = next(iter(tags))
        if tag == 'eval' and not os.path.exists(os.path.join(K, 'ctl', 'EVAL_OK')): return 'eval job without ctl/EVAL_OK'
        scenes = [s for t in tasks for s in ((t.get('meta') or {}).get('scenes') or [])]
        if tag == 'train':
            if not all((t.get('meta') or {}).get('scenes') for t in tasks): return 'train task without meta.scenes'
            try: excl.assert_train(sorted(set(scenes)))
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
cat > $K/kit/c2_jobs.py.new <<'PYEOF'
"""nvkey1 C2: pointing-row audit tasks. One call = up to CHUNK rows of one clip, each row one frame (a red ring at the row's point for a visible
row; no ring for an absent row) and its claim. Rows: the pointing store rows whose frame is on this node, minus the K1-heldout removal list.
usage: c2_jobs.py OUT.jsonl MODEL EFFORT [CHUNK=40] [ROWS=all|path to a json list of store indices]  (C1_EXTRA env adds request fields)
nvkey2: every task carries meta.tag (dev-analysis when the clip's scene hits the exclusion lists, else train) and meta.scenes; one tag per output job
(the builder refuses a mix); K/c2_rows_meta.json is merged, never replaced."""
import json, os, sys, sqlite3, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
STORE = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
HELD = '/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl'
ROOTS = ['/scratch/jjyeung/k1_frames', '/scratch/jjyeung/devs1_frames']
PROMPT = ('You are auditing labels of a pointing dataset. Each row below shows one video frame of an indoor room and one claim about it.\n'
          '- A "point" row has a red ring drawn on the image. Its claim: the centre of the ring lies on a visible part of an object of the named kind.\n'
          '- An "absent" row has no ring. Its claim: no object of the named kind is visible anywhere in the image.\n'
          'Judge every claim from its image alone, and answer for each row:\n'
          '"present": is at least one object of the named kind visible in the image, fully or partly? true or false.\n'
          '"on_object": point rows only: is the centre of the ring on a visible part of an object of the named kind? true or false; null for absent rows.\n'
          '"name_fits": point rows only: would most people call the object under the centre of the ring by the given name or a close synonym? true or false; null for absent rows.\n'
          '"point": when present is true and the claim is wrong (an absent row, or on_object false), one point on a visible part of the named object as [x, y] '
          'in 0-1000 image coordinates (x = 0 left edge, 1000 right edge; y = 0 top edge, 1000 bottom edge); otherwise null.\n'
          'Reply with one JSON object and nothing else: {{"<row id>": {{"present": ..., "on_object": ..., "name_fits": ..., "point": ...}}, ...}} with all {n} row ids.')
def frame_path(sha):
    for r in ROOTS:
        p = '%s/%s/%s.png' % (r, sha[:2], sha)
        if os.path.exists(p): return p
def held_ids():
    s = set()
    if os.path.exists(HELD):
        for l in open(HELD):
            try:
                d = json.loads(l); k = d.get('row_key') or d.get('qid')
                if k: s.add(str(k))
            except Exception: pass
    return s
def load_rows(only=None):
    c = sqlite3.connect('file:%s?mode=ro' % STORE, uri=True); held = held_ids(); out = []; nheld_rows = [0]
    for i, s in c.execute('select i,row from rows'):
        if only is not None and i not in only: continue
        d = json.loads(s); p = d['pointing']; f = frame_path(p.get('rgb_sha256') or '')
        if not f: continue
        if d.get('qid') in held: nheld_rows[0] += 1; continue
        out.append(dict(i=i, qid=d.get('qid'), scene=d['scene'], dataset=d['dataset'], kind=p['kind'], label=p['label'], frame=p['frame'], area=p.get('area_fraction') or 0.0,
                        stratum=p.get('stratum'), uv=(p.get('selected') or {}).get('uv'), path=f, canonical=(d.get('provenance') or {}).get('canonical_scene')))
    print('held-out list keys', len(held), 'local rows dropped as K1-heldout', nheld_rows[0])
    return out, len(held)
def main():
    out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    only = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 and sys.argv[5] != 'all' else None
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); tag = model.split('/')[-1]
    rows, nheld = load_rows(only); byc = collections.defaultdict(list)
    for r in rows: byc[r['scene']].append(r)
    rng = random.Random(20261120); n = 0; meta_rows = {}; tags = set()
    with open(out, 'a') as f:
        for sc in sorted(byc):
            rs = byc[sc][:]; rng.shuffle(rs)
            for j in range(0, len(rs), chunk):
                part = rs[j:j + chunk]; content = [{'text': PROMPT.format(n=len(part))}]
                for r in part:
                    rid = 'r%d' % r['i']
                    if r['kind'] == 'gt_absent':
                        content += [{'text': 'Row %s (absent row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640}]
                    else:
                        content += [{'text': 'Row %s (point row): kind = "%s"' % (rid, r['label'])}, {'image': r['path'], 'max_side': 640, 'mark': r['uv']}]
                can = part[0]['canonical'] or '%s/%s' % (part[0]['dataset'], sc); rtag = 'dev-analysis' if excl.reasons(can) else 'train'
                tags.add(rtag); assert len(tags) == 1, 'mixed train and dev-analysis clips: build them as two jobs'
                if rtag == 'train': excl.assert_train([can])
                f.write(json.dumps({'id': 'c2_%s_%d_%s' % (sc, j // chunk, tag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                                    'content': content, 'meta': {'scene': sc, 'rows': [r['i'] for r in part], 'tag': rtag, 'scenes': [can]}}) + '\n'); n += 1
                for r in part: meta_rows[r['i']] = {k: r[k] for k in ('qid', 'scene', 'dataset', 'kind', 'label', 'frame', 'area', 'stratum', 'uv', 'canonical')}
    mp = K + '/c2_rows_meta.json'; old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update({str(k): v for k, v in meta_rows.items()}); json.dump(old, open(mp + '.tmp', 'w')); os.replace(mp + '.tmp', mp)
    print('rows', len(rows), 'clips', len(byc), 'tasks', n, 'heldout ids in list', nheld, 'kinds', dict(collections.Counter(r['kind'] for r in rows)))
if __name__ == '__main__': main()
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
cat meter/METER.json; tmux ls 2>&1 | grep nvk
$P -B - <<'PY'
import json
for l in open('queue/10_bake32.jsonl'):
    t = json.loads(l)
    if 'opus' in t['model']: print('opus task', t['model'], t.get('effort'), t.get('extra'), t.get('max_tokens')); break
PY
mkdir -p queue_done analysis_only/out
cp -p kit/nvrun.py kit/nvrun.py.v1_nvkey1; cp -p kit/c2_jobs.py kit/c2_jobs.py.v1_nvkey1
mv kit/nvrun.py.new kit/nvrun.py; mv kit/c2_jobs.py.new kit/c2_jobs.py
for j in 05_smoke 10_bake32 20_c0census32 30_c1rest32 31_c1all64 41_c2audit; do mv queue/$j.jsonl queue_done/; done
mv queue/40_c2audit.jsonl.bad_heldout_filter queue_done/
mv out/20_c0census32.jsonl analysis_only/out/; mv out/41_c2audit.jsonl analysis_only/out/
echo "analysis_only: dev-S1 census points and summaries (C0); no row or alias builder reads this folder" > c0/ANALYSIS_ONLY.md
ls queue queue_done analysis_only/out out
$P -B - <<'PY'
import json
d = json.load(open('c2/THIRD_ROWS.json')); rows = sorted(set(d['candidates']) | set(d['controls'])); print('third rows', len(rows), len(d['candidates']), len(d['controls']))
json.dump(rows, open('c2/THIRD_ROWS_list.json', 'w'))
PY
C1_EXTRA='{}' $P -B kit/c2_jobs.py queue/.42_c2third.tmp azure/anthropic/claude-opus-5-5 high 40 c2/THIRD_ROWS_list.json && mv queue/.42_c2third.tmp queue/42_c2third.jsonl
$P -B -c "
import json
ts=[json.loads(l) for l in open('queue/42_c2third.jsonl')]; print('tasks', len(ts), 'rows', sum(len(t['meta']['rows']) for t in ts), set(t['meta']['tag'] for t in ts), ts[0]['meta']['scenes'], ts[0]['effort'], ts[0]['model'])"
tmux kill-session -t nvk1_run 2>/dev/null; sleep 1
tmux new-session -d -s nvk1_run "cd $K && SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt NVK=$K /scratch/jjyeung/envs/p1cpu/bin/python -B kit/nvrun.py 3600 </dev/null >>$K/runner.stdout 2>&1" </dev/null >/dev/null 2>&1
sleep 20; tmux ls | grep nvk; tail -4 runner.log; tail -3 runner.stdout
