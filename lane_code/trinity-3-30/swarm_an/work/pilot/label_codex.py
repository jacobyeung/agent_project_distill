"""Codex Astra labeller for the labelling pilot (lane swarm_an; ORCH ANSWER 06:58Z): one read-only dispatch per clip, which opens the
clip's four contact sheets and answers every closed question in questions.json as one JSON object. Truth is never in the folder.
usage: /usr/bin/python3 label_codex.py --jobs JOBS.json --tag TAG [--par 4] [--only clip,clip] [--limit N] [--effort medium]
JOBS.json: {clip: {"sheets": [absolute jpg paths], "questions": [{"qid", "text", "format"}]}}  (same file as label.py, the Gemini driver)
Results: work/pilot/results/TAG/<clip>.json; one line per dispatch in work/pilot/CALLS_CODEX.log (cap 250 for the pilot).
Receipts: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/<stamp>_lab_TAG_<clip>/final_message.md."""
import argparse, concurrent.futures, datetime, glob, io, json, os, re, subprocess, sys, time
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'
B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'
CR = '/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/'
CAP = 250
ap = argparse.ArgumentParser()
ap.add_argument('--jobs'); ap.add_argument('--tag'); ap.add_argument('--par', type=int, default=4); ap.add_argument('--only', default='')
ap.add_argument('--limit', type=int, default=0); ap.add_argument('--effort', default='medium'); ap.add_argument('--timeout', type=int, default=1500)
a = ap.parse_args()
jobs = json.load(open(a.jobs)); out = P + 'results/' + a.tag + '/'; lab = P + 'lab/' + a.tag + '/'
os.makedirs(out, exist_ok=True)
def calls():
    try: return sum(1 for _ in open(P + 'CALLS_CODEX.log'))
    except IOError: return 0
def prompt(clip, job, folder):
    L = ['# Labeller lab_%s_%s: answer closed questions about one video clip from its frames (read-only)' % (a.tag, clip), '',
         'Rules: read-only; no ssh, network, Git or deletion; open only the files named here; do not search for other files, for answers or for any metadata about this clip; no subagents.', '',
         'The clip is 32 frames sampled in time order from one video of a room. The frames are shown on four contact sheets, eight frames per sheet, and every tile carries its frame number ("frame 1" to "frame 32") in its top-left corner:']
    for k, s in enumerate(job['sheets']): L.append('- `%s` (frames %d to %d)' % (s, 8 * k + 1, 8 * k + 8))
    L += ['', 'Open each of the four images with your image-viewing tool (view the local image file by its path) and look at every frame. "Frame k" in a question means the tile labelled "frame k".',
          'Then answer every question in `%s/questions.json` (a list of objects with `qid`, `text` and `format`) from the frames alone. Give your best answer to every question; never leave one out.' % folder, '',
          'Your final message must be exactly one JSON object and nothing else (no prose, no code fence): every `qid` as a key with its answer in the stated format, plus the key `"check"` whose value is one sentence that says what frame 5 and frame 30 show (the main objects and their colours). If you cannot view the images, reply `{"error": "<why>"}` and stop.']
    return '\n'.join(L) + '\n'
def parse(txt):
    m = re.search(r'\{.*\}', txt or '', re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except ValueError: return None
def one(clip):
    job = jobs[clip]; res = out + clip + '.json'
    if os.path.isfile(res) and (json.load(open(res)).get('answers') or {}).get('check'): return clip, 'cached'
    if calls() >= CAP: return clip, 'cap reached'
    folder = lab + clip; os.makedirs(folder, exist_ok=True)
    json.dump(job['questions'], open(folder + '/questions.json', 'w'), indent=1)
    pf = folder + '/PROMPT.md'; io.open(pf, 'w', encoding='utf-8').write(prompt(clip, job, folder))
    label = 'lab_%s_%s' % (a.tag, clip); t0 = time.time()
    cmd = ['bash', B + '/tools/codex_local.sh', 'review', folder, pf, '--model', 'gpt-6-astra', '--effort', a.effort, '--label', label, '--skip-git-check']
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=a.timeout); code = p.returncode; tail = p.stdout.decode('utf-8', 'replace')[-500:]
    except subprocess.TimeoutExpired:
        code, tail = -9, 'timeout'
    rec = sorted(glob.glob(CR + '*_' + label)); txt = ''
    if rec and os.path.isfile(rec[-1] + '/final_message.md'): txt = io.open(rec[-1] + '/final_message.md', encoding='utf-8', errors='replace').read()
    ans = parse(txt); sec = time.time() - t0
    json.dump(dict(clip=clip, tag=a.tag, model='gpt-6-astra', effort=a.effort, answers=ans, raw=txt[-3000:], exit=code, tail=tail, seconds=round(sec, 1),
                   receipt=rec[-1] if rec else None, questions=len(job['questions'])), open(res, 'w'), indent=0)
    with open(P + 'CALLS_CODEX.log', 'a') as f:
        f.write('%s %s %s exit=%s sec=%.0f answers=%s questions=%d\n' % (datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'), a.tag, clip, code, sec,
                len(ans) if isinstance(ans, dict) else None, len(job['questions'])))
    return clip, 'ok' if isinstance(ans, dict) and 'error' not in ans else 'no answers (exit %s)' % code
clips = [c for c in sorted(jobs) if not a.only or c in a.only.split(',')]
if a.limit: clips = clips[:a.limit]
with concurrent.futures.ThreadPoolExecutor(a.par) as ex:
    for clip, st in ex.map(one, clips): print(clip, st); sys.stdout.flush()
print('dispatches logged so far:', calls())
