"""Batched labeller for the labelling pilot (lane swarm_an): one gemini-agent run per clip, which reads the clip's contact sheets
once and answers every closed question about that clip as one JSON object. Truth is never in the prompt.
usage: /usr/bin/python3 label.py --jobs JOBS.json --model hydrogen|gemini-4-argon --tag TAG [--par 3] [--limit N] [--effort LEVEL]
JOBS.json: {clip: {"sheets": [absolute jpg paths], "questions": [{"qid": "Q1", "text": "...", "format": "..."}]}}
Results: work/pilot/results/TAG/<clip>.json; one line per run in work/pilot/CALLS.log (the pilot's cap is 300 runs in all).
Run folders (transcripts hold the images) go to /tmp/swarm_an_pilot_runs and are not kept."""
import argparse, concurrent.futures, datetime, io, json, os, re, subprocess, sys, time
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'
RUNS = '/tmp/swarm_an_pilot_runs/'
CAP = 300
ap = argparse.ArgumentParser()
ap.add_argument('--jobs'); ap.add_argument('--model'); ap.add_argument('--tag'); ap.add_argument('--par', type=int, default=3)
ap.add_argument('--limit', type=int, default=0); ap.add_argument('--effort', default=''); ap.add_argument('--timeout', type=int, default=900)
a = ap.parse_args()
jobs = json.load(open(a.jobs)); out = P + 'results/' + a.tag + '/'
os.makedirs(out, exist_ok=True); os.makedirs(RUNS, exist_ok=True)
def calls():
    try: return sum(1 for _ in open(P + 'CALLS.log'))
    except IOError: return 0
def prompt(clip, job):
    L = ['You are labelling one indoor video clip. The clip is 32 frames sampled in time order from one video of a room. '
         'The frames are shown on four contact sheets, eight frames per sheet, and every tile carries its frame number ("frame 1" to "frame 32") in its top-left corner:']
    for k, s in enumerate(job['sheets']): L.append('- %s (frames %d to %d)' % (s, 8 * k + 1, 8 * k + 8))
    L.append('Read these four image files with the Read tool, one call per file, and use no other tool and no other file. '
             'Then answer every question below from the frames alone. "Frame k" in a question means the tile labelled "frame k".')
    L.append('Questions:')
    for q in job['questions']: L.append('%s. %s\n   Answer format: %s' % (q['qid'], q['text'], q['format']))
    L.append('Reply with ONLY one JSON object that has every question id as a key, for example {"Q1": "A", "Q2": 3}. No prose, no code fence, no explanation.')
    return '\n'.join(L)
def parse(txt):
    m = re.search(r'\{.*\}', txt or '', re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except ValueError:
        try: return json.loads(re.sub(r',\s*\}', '}', m.group(0)))
        except ValueError: return None
def one(clip):
    job = jobs[clip]; res = out + clip + '.json'
    if os.path.isfile(res) and json.load(open(res)).get('answers'): return clip, 'cached'
    if calls() >= CAP: return clip, 'cap reached'
    stamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'); rd = RUNS + '%s_%s_%s' % (a.tag, clip, stamp)
    pf = RUNS + '%s_%s_prompt.md' % (a.tag, clip); io.open(pf, 'w', encoding='utf-8').write(prompt(clip, job))
    cmd = ['gemini-agent', '--read-only', '--model', a.model, '-C', os.path.dirname(job['sheets'][0]), '-f', pf, '--run-dir', rd]
    if a.effort: cmd += ['--effort', a.effort]
    cmd += ['--', '--max-turns', '12']
    t0 = time.time()
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=a.timeout); code = p.returncode
        txt = p.stdout.decode('utf-8', 'replace'); err = p.stderr.decode('utf-8', 'replace')[-400:]
    except subprocess.TimeoutExpired:
        code, txt, err = -9, '', 'timeout'
    meta = {}
    try: meta = json.load(open(rd + '/meta.json'))
    except Exception: pass
    use = {}
    try:
        for l in open(rd + '/transcript.jsonl'):
            if '"usage"' not in l: continue
            d = json.loads(l); u = (d.get('message') or {}).get('usage') or d.get('usage') or {}
            if d.get('type') == 'result' and u: use = u
    except Exception: pass
    ans = parse(txt)
    json.dump(dict(clip=clip, model=a.model, tag=a.tag, answers=ans, raw=txt[-3000:], exit=code, stderr=err, seconds=round(time.time() - t0, 1),
                   meta=dict((k, meta.get(k)) for k in ('is_error', 'num_turns', 'duration_ms', 'total_cost_usd', 'usage')), usage=use,
                   questions=len(job['questions'])), open(res, 'w'), indent=0)
    with open(P + 'CALLS.log', 'a') as f:
        f.write('%s %s %s %s exit=%s turns=%s sec=%.0f answers=%s in=%s out=%s\n' % (stamp, a.tag, clip, a.model, code, meta.get('num_turns'), time.time() - t0,
                len(ans) if isinstance(ans, dict) else None, use.get('input_tokens'), use.get('output_tokens')))
    return clip, 'ok' if isinstance(ans, dict) else 'no json (exit %s)' % code
clips = sorted(jobs)[:a.limit] if a.limit else sorted(jobs)
with concurrent.futures.ThreadPoolExecutor(a.par) as ex:
    for clip, st in ex.map(one, clips): print(clip, st); sys.stdout.flush()
print('runs logged so far:', calls())
