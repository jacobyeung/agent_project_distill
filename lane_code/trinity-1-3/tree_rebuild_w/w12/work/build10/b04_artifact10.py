"""Build only synthetic fixture weights; trained head tensors are read-only mounts."""
from pathlib import Path
import hashlib,json,sys,shutil,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
sys.path[:0]=[str(B/'b04_stage'),str(B),str(L/'work/tree_r1')]
from eat1_adapter import b04_tiny as F
from safetensors.torch import save_file
from transformers import AutoTokenizer,Qwen3Config,Qwen3ForCausalLM
from types import SimpleNamespace as NS
from student_pilot.carrier_c1_routing import add_routing_tokens
from e2e_reader import artifact as A
from eat1.artifact import write_manifest
import torch,numpy as np
art=L/'work/build12/proofs/eat1/b04/reader/artifact';art.mkdir(parents=True,exist_ok=True)
tok=AutoTokenizer.from_pretrained(F.TOK);add_routing_tokens(NS(tokenizer=tok));tok.save_pretrained(art/'tokenizer')
torch.manual_seed(0)
cfg=Qwen3Config(vocab_size=len(tok),hidden_size=32,intermediate_size=64,num_hidden_layers=2,
    num_attention_heads=2,num_key_value_heads=1,head_dim=16,max_position_embeddings=4096)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
Qwen3ForCausalLM(cfg).eval().save_pretrained(art/'checkpoint',safe_serialization=True)
z=np.load(F.K1/'tower.npz');receipt=json.loads((F.K1/'PHASE_COMPLETE.json').read_text())
g3t=F.FixtureG3T({k:z[k] for k in F.TOWER_KEYS},receipt['source_hw'])
save_file({k:v.contiguous() for k,v in g3t.state_dict().items()},str(art/'g3t_fixture.safetensors'))
save_file(F.FixtureSAM3((F.K1/'candidates.json').read_bytes()).state_dict(),str(art/'sam3_fixture.safetensors'))
rel=lambda d:sorted(str(p.relative_to(art)) for p in (art/d).iterdir())
components=dict(lm=('checkpoint',rel('checkpoint')),tokenizer=('tokenizer',rel('tokenizer')),
    g3t=('g3t',['g3t_fixture.safetensors']),sam3=('sam3',['sam3_fixture.safetensors']),
    scale_head=('scale_head',rel('scale_head')),selector_head=('selector_head',rel('selector_head')))
manifest=A.build_manifest(art,components,code_roots=F.CODE_ROOTS)
_,digest=A.write_manifest(art,manifest)
roles={r:('lm' if k=='lm' else 'tokenizer' if k=='tokenizer' else 'tower' if k in ('g3t','sam3') else 'head')
       for k,(_,paths) in components.items() for r in paths}
write_manifest(art/'ARTIFACT.json',art,roles,F.MODULES)
(art/'E2E_MANIFEST.sha256').write_text(digest+'\n')
print('Synthetic artifact prepared; trained head files remain read-only mounts.')
