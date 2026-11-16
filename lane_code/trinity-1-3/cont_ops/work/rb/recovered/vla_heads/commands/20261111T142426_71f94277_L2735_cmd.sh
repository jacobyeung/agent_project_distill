<!-- recovered by seal_plan: transcript=71f94277 line=2735 utc=2026-11-11T14:24:26.582Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/vla_design_review && python3 - <<'EOF'
p='VLA_SCHEMA.md'; L=open(p).read().split('\n'); n=0
for i,l in enumerate(L):
    if l.startswith('- FAST fixture (`fast_fixture_v2`)'):
        L[i]=l+' Pinned (lane vla_heads, 2026-11-11T14:24Z): /scratch/jjyeung/orch_cd/vla_heads/out/fast_fixture_v2.json, sha256 cab2442cc376ab1ee68f13097bce41462b2db0d1655152a086a04df3e00352b5, tokenizers 0.22.2 (transformers 5.12.1, scipy 1.14.1), min_token -28, max_token 28, 736 BPE symbols; a refit is byte-identical.'; n+=1
    if l.startswith('- `fast` integer stage'):
        L[i]=l+' With the pinned fixture, example 7 encodes to BPE ids [34, 362, 85, 199, 118, 123, 718, 54, 207] and LM ids [247053, 247381, 247104, 247218, 247137, 247142, 247737, 247073, 247226] followed by the end id 248043; T-12 asserts exactly these.'; n+=1
assert n==2, n
open(p,'w').write('\n'.join(L)); print('pinned')
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: vla_heads RESULT 1424Z: schema v2 implemented (137 CPU tests, 376 s; archive out/vla_heads_20261111T1422Z.tar); conformance T-1 (head side), T-2, T-5, T-8, T-9, T-12 pass; default head = StarVLA OFT form (168M at hidden 4096), flow expert 146M, FAST tokens 9.5M; FAST fixture pinned (sha256 cab2442c..., tokenizers 0.22.2) and example 7's BPE and LM-id sequences written into VLA_SCHEMA.md by me: the final check's fourth point is closed. Schema v2 is complete." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md