import json, os, sys
os.environ['PART2_STAGED'] = '1'
sys.path.insert(0, sys.argv[1] + '/sb_mask_phrase/part2')
import sam3_pass as G
out = {}
for name, aliases in (('default', False), ('all_aliases', True)):
    p = G.plan(aliases)
    calls = sum(G.distinct(k) for _, k in p)
    new = json.loads(G.NEW.read_text())['phrases']
    calls_wo_new = sum(G.distinct(k, new) for _, k in p)
    raw = sum(len(k) for _, k in p)
    out[name] = dict(captures=len(p), calls=calls, calls_without_new=calls_wo_new, raw_name_calls=raw,
                     gpu_h_spec_rate=calls*32*.064/3600, gpu_h_without_new=calls_wo_new*32*.064/3600,
                     per_capture_mean=calls/len(p), first=p[0][0]['canonical'], first_calls=p[0][1])
step5 = [k for c, k in G.plan() if c['canonical'] == G.STEP5_CAPTURE][0]
out['step5_capture'] = dict(name=G.STEP5_CAPTURE, names=len(step5), calls=step5)
out['new_phrases'] = dict(names=len(new), phrases=sum(map(len, new.values())))
out['chosen'] = G.chosen_phrases()
print(json.dumps(out, indent=1))
