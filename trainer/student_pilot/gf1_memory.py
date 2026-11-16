"""Shape budget, not a measured CUDA peak; SDPA and layer checkpointing assumed."""
import argparse
import json


def estimate(frames,stage,bank_layers=3,hidden=1024):
    # Explicit 9B envelope; replace parameter counts with the launch checkpoint inventory.
    base_params=9_000_000_000; lm_dim=4096; layers=32; mlp=12288; vocab=248320
    tower_params=1_200_000_000; own_params=500_000_000
    dense=max(64,frames); seq=130*frames+1024; patches=37*37
    connector=bank_layers*(2*2048+2048*hidden+hidden)+hidden*lm_dim
    fixed=dict(base_weights_optimizer=(base_params*2/4 if stage==1 else base_params*16/4),
        frozen_tower=tower_params*2,own_heads=(own_params*4 if stage==1 else own_params*16),
        connector_weights_grad_adam=connector*16)
    dynamic=dict(dense_rgb=dense*3*518*518*4,
        camera_rgb=32*3*518*518*4,
        camera_selected_bank=bank_layers*32*patches*2048*2,
        dense_selected_bank=bank_layers*dense*patches*2048*2,
        tower_working=dense*(patches+5)*1024*2*12,
        connector_raw_bank=bank_layers*frames*patches*2048*2,
        connector_projection_work=frames*patches*(2048+hidden)*4*3,
        lm_checkpoint_inputs=layers*seq*lm_dim*2,
        lm_layer_work=seq*(lm_dim*10+mlp*6)*2,
        assistant_logits=1024*vocab*4,
        fsdp_layer_gather=2*(4*lm_dim**2+3*lm_dim*mlp)*(2 if stage==1 else 4))
    # Sum simultaneous envelopes conservatively, then reserve 20% for allocator/kernel variation.
    total=sum(fixed.values())+sum(dynamic.values())
    return dict(frames=frames,dense_frames=dense,visual_tokens=frames*130,stage=stage,
        world_size=4, supported=frames==32, camera_frames=32,
        second_pass_cost=dict(dense_tokens=dense*(patches+5), camera_tokens=32*(patches+5),
            tokenwise_fraction=32/dense, global_attention_fraction=(32/dense)**2, shared_parameters=True),
        parameter_assumptions=dict(base=base_params,tower=tower_params,own_heads=own_params,connector=connector),
        tensor_assumptions=dict(lm_hidden=lm_dim,lm_layers=layers,mlp=mlp,bank_layers=bank_layers,patch_grid=[37,37],
                                qwen_merger_grid=[10,13],text_tokens=1024,attention='memory-efficient SDPA; no N squared materialization'),
        fixed_GiB={k:round(v/2**30,4) for k,v in fixed.items()},dynamic_GiB={k:round(v/2**30,4) for k,v in dynamic.items()},
        estimate_GiB=round(total*1.2/2**30,2),measured=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bank-layers',type=int,default=3)
    args=parser.parse_args()
    print(json.dumps(dict(caveat='Envelope only; Only 32 LM frames are supported. Excludes hybrid-attention state, routed FP32 tower/heads and loading peak, decoder-side 0/1/2 storage, long tool traces and eager attention. Requires GPU peak calibration before training.',
        rows=[estimate(f,s,args.bank_layers) for s in (1,2) for f in (32,64,96,128)]),indent=2))
if __name__=='__main__':main()
