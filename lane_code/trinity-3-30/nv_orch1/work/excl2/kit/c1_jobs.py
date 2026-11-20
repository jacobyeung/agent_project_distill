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
    if len(sys.argv) < 5: return
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
if __name__ == '__main__': main()
