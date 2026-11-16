from pathlib import Path
p=Path('code/report.py');s=p.read_text();s=s.replace('def build(merged_path,output,comparators=()):','def build(merged_path,output,comparators=(),proof_path=None,release_path=None):')
s=s.replace("    enriched=[dict(r,",'''    proof_pin=pin(proof_path) if proof_path else bundle.get('proof')
    proof=load(checked(proof_pin)) if proof_pin else None
    if not bundle['synthetic'] and (not proof or proof.get('synthetic') is not False or proof.get('items')!=10):
        raise ValueError('non-synthetic report requires the in-job ten-item proof')
    if not bundle['synthetic'] and (bundle.get('proof')!=proof_pin or proof.get('read_binding')!=bundle['request_binding']):
        raise ValueError('proof does not bind this read')
    release=load(release_path) if release_path else dict(status='not run',compared_frames=0,identical_frames=0)
    frame_note="Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: "+release['status']+f"; {release['identical_frames']}/{release['compared_frames']} identical frames."
    proof_note=('In-job dev-S1 proof: '+str(proof['identical_count'])+'/10 identical; equal token-sequence share '+str(proof['equal_token_share'])+'; first divergences '+json.dumps([{r['key']:r['first_divergence']} for r in proof['records'] if r['first_divergence']],sort_keys=True)+'.') if proof else 'In-job dev-S1 proof: not run (synthetic rehearsal).'
    enriched=[dict(r,''')
s=s.replace("source=pin(merged_path),disclosure=DISCLOSURE", "source=pin(merged_path),proof=proof,proof_source=proof_pin,proof_summary=proof_note,frames=frame_note,release_check=release,disclosure=DISCLOSURE")
s=s.replace("text=[heading+'\\n',", "text=[heading+'\\n',proof_note+'\\n',frame_note+'\\n',")
p.write_text(s)
p=Path('code/entry.py');s=p.read_text().replace("    q=sub.add_parser('proof')", "    q.add_argument('--proof');q.add_argument('--release-check')\n    q=sub.add_parser('proof')").replace('return build(a.merged,a.out,a.comparators)','return build(a.merged,a.out,a.comparators,a.proof,a.release_check)');p.write_text(s)
